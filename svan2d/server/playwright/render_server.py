"""FastAPI-based rendering server using Playwright with persistent browser pool.

Maintains a single browser instance with a pool of reusable pages for efficient
batch rendering. Eliminates browser launch overhead (~200ms) per request.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from playwright.async_api import async_playwright, Browser, Page, Playwright
from svan2d.core.logger import get_logger

logger = get_logger()


class RenderRequest(BaseModel):
    """Request model for /render endpoint"""

    svg: str
    type: Literal["png", "pdf"]
    width: int
    height: int


class BrowserPool:
    """Manages a persistent browser with a pool of reusable pages.

    Pages are created on-demand up to max_pages, then reused via an async queue.
    This eliminates browser launch overhead and reduces page creation overhead.
    """

    def __init__(self, max_pages: int = 4):
        self.max_pages = max_pages
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page_pool: asyncio.Queue[Page] = asyncio.Queue()
        self._pages_created = 0
        self._lock = asyncio.Lock()

    async def start(self):
        """Initialize browser on server startup."""
        logger.info("Starting Playwright browser pool...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        logger.info(f"Browser pool ready (max_pages={self.max_pages})")

    async def stop(self):
        """Clean up browser on server shutdown."""
        logger.info("Stopping browser pool...")
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser pool stopped")

    @asynccontextmanager
    async def acquire_page(self):
        """Acquire a page from the pool, creating one if needed.

        Usage:
            async with pool.acquire_page() as page:
                await page.set_content(...)
                png = await page.screenshot()
        """
        page = None
        try:
            # Try to get an existing page from pool (non-blocking)
            try:
                page = self._page_pool.get_nowait()
            except asyncio.QueueEmpty:
                # No page available, create one if under limit
                assert self._browser is not None
                async with self._lock:
                    if self._pages_created < self.max_pages:
                        page = await self._browser.new_page()
                        self._pages_created += 1
                        logger.debug(
                            f"Created new page ({self._pages_created}/{self.max_pages})"
                        )
                    else:
                        # At limit, wait for a page to be returned
                        page = await self._page_pool.get()

            yield page

        finally:
            # Return page to pool for reuse
            if page:
                try:
                    # Clear page state for next use
                    await page.set_content("<html><body></body></html>")
                    await self._page_pool.put(page)
                except Exception as e:
                    # Page is broken, create fresh one next time
                    logger.warning(f"Failed to reset page, discarding: {e}")
                    async with self._lock:
                        self._pages_created -= 1

    @property
    def stats(self) -> dict:
        """Return pool statistics."""
        return {
            "pages_created": self._pages_created,
            "max_pages": self.max_pages,
            "pages_available": self._page_pool.qsize(),
        }


# Global browser pool instance
# Max pages configurable via environment variable
_max_pages = int(os.environ.get("SVAN2D_PLAYWRIGHT_MAX_PAGES", "4"))
browser_pool = BrowserPool(max_pages=_max_pages)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage browser lifecycle with FastAPI lifespan."""
    await browser_pool.start()
    yield
    await browser_pool.stop()


app = FastAPI(
    title="Svan2D Playwright Render Server",
    description="HTTP server for rendering SVG to PNG/PDF using Playwright (pooled)",
    version="2.0.0",
    lifespan=lifespan,
)


@app.post("/render")
async def render(request: RenderRequest) -> Response:
    """Render SVG to PNG or PDF using pooled browser page.

    Args:
        request: RenderRequest with svg content, type, width, height

    Returns:
        Binary PNG or PDF data

    Raises:
        HTTPException: If rendering fails or invalid type provided
    """
    if not request.svg or not request.type or not request.width or not request.height:
        raise HTTPException(
            status_code=400, detail="Missing svg, type, width, or height"
        )

    timestamp = datetime.now().isoformat()
    logger.debug(
        f"[{timestamp}] Render request: {request.type} {request.width}x{request.height}"
    )

    try:
        async with browser_pool.acquire_page() as page:
            # Set viewport and load SVG content
            await page.set_viewport_size(
                {"width": request.width, "height": request.height}
            )
            html_content = (
                f'<html><body style="margin:0;padding:0;">{request.svg}</body></html>'
            )
            await page.set_content(html_content)
            await page.wait_for_load_state("domcontentloaded")

            # Render based on type
            if request.type == "png":
                buffer = await page.screenshot(full_page=True)
                content_type = "image/png"
            elif request.type == "pdf":
                buffer = await page.pdf(
                    width=f"{request.width}px",
                    height=f"{request.height}px",
                    print_background=True,
                    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                )
                content_type = "application/pdf"
            else:
                raise HTTPException(
                    status_code=400, detail=f"Unknown render type: {request.type}"
                )

        return Response(content=buffer, media_type=content_type)

    except Exception as err:
        timestamp_error = datetime.now().isoformat()
        logger.error(f"[{timestamp_error}] Render error: {err}")
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring server status."""
    return {
        "status": "ok",
        "service": "playwright-render-server",
        "pool": browser_pool.stats,
    }


@app.get("/stats")
async def pool_stats():
    """Return detailed pool statistics."""
    return browser_pool.stats


def create_server(host: str = "localhost", port: int = 4000):
    """Create and configure the FastAPI server.

    Args:
        host: Host to bind to (default: localhost)
        port: Port to listen on (default: 4000)

    Returns:
        Configured FastAPI app
    """
    return app


if __name__ == "__main__":
    import uvicorn

    # Run server directly for testing
    uvicorn.run(app, host="localhost", port=4000, log_level="info")
