"""FastAPI-based rendering server using Playwright with persistent browser pool.

Maintains a single browser instance with a pool of reusable pages for efficient
batch rendering. Eliminates browser launch overhead (~200ms) per request.
"""

from __future__ import annotations

import asyncio
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from playwright.async_api import async_playwright, Browser, Page, Playwright
from svan2d.core.logger import get_logger

logger = get_logger()


class RenderRequest(BaseModel):
    """Request model for /render endpoint supporting SVG, HTML, and Assets"""

    svg: Optional[str] = None
    html: Optional[str] = None
    type: Literal["png", "pdf", "svg_fragment"]
    width: int
    height: int
    assets: Optional[Dict[str, str]] = None


class BrowserPool:
    """Manages a persistent browser with a pool of reusable pages."""

    def __init__(self, max_pages: int = 4):
        self.max_pages = max_pages
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
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

    async def _ensure_browser(self):
        """Relaunch the browser (and reset the pool) if it has died."""
        if self._browser is not None and self._browser.is_connected():
            return
        async with self._lock:
            # Re-check under lock; another coroutine may have healed it.
            if self._browser is not None and self._browser.is_connected():
                return
            logger.warning("Browser is down — relaunching pool")
            if self._browser is not None:
                try:
                    await self._browser.close()
                except Exception:
                    pass
            # Drain now-dead pages and reset the counter.
            while not self._page_pool.empty():
                try:
                    self._page_pool.get_nowait()
                except asyncio.QueueEmpty:
                    break
            self._pages_created = 0
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            logger.info("Browser relaunched")

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
        """Acquire a page from the pool, creating one if needed."""
        await self._ensure_browser()
        page = None
        try:
            while page is None:
                try:
                    candidate = self._page_pool.get_nowait()
                except asyncio.QueueEmpty:
                    candidate = None

                if candidate is not None:
                    if candidate.is_closed():
                        async with self._lock:
                            self._pages_created -= 1
                        continue
                    page = candidate
                    break

                async with self._lock:
                    if self._pages_created < self.max_pages:
                        page = await self._browser.new_page()
                        self._pages_created += 1
                        logger.debug(
                            f"Created new page ({self._pages_created}/{self.max_pages})"
                        )

                if page is None:  # pool full, wait for a returned page
                    page = await self._page_pool.get()
                    if page.is_closed():
                        async with self._lock:
                            self._pages_created -= 1
                        page = None

            yield page

        finally:
            if page is not None:
                try:
                    if page.is_closed():
                        async with self._lock:
                            self._pages_created -= 1
                    else:
                        # Clear page and routes for reuse
                        await page.unroute("**/*")
                        await page.set_content("<html><body></body></html>")
                        await self._page_pool.put(page)
                except Exception as e:
                    logger.warning(f"Failed to reset page, discarding: {e}")
                    try:
                        await page.close()
                    except Exception:
                        pass
                    async with self._lock:
                        self._pages_created -= 1

    @property
    def is_healthy(self) -> bool:
        return self._browser is not None and self._browser.is_connected()

    @property
    def stats(self) -> dict:
        return {
            "pages_created": self._pages_created,
            "max_pages": self.max_pages,
            "pages_available": self._page_pool.qsize(),
        }


_max_pages = int(os.environ.get("SVAN2D_PLAYWRIGHT_MAX_PAGES", "4"))
browser_pool = BrowserPool(max_pages=_max_pages)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await browser_pool.start()
    yield
    await browser_pool.stop()


app = FastAPI(
    title="Svan2D Playwright Render Server",
    description="HTTP server for rendering SVG/HTML using Playwright (pooled)",
    version="2.1.0",
    lifespan=lifespan,
)


@app.post("/render")
async def render(request: RenderRequest) -> Response:
    """Render content using pooled browser page with explicit asset mapping."""

    if not (request.svg or request.html):
        raise HTTPException(status_code=400, detail="Missing svg or html content")

    timestamp = datetime.now().isoformat()
    logger.debug(
        f"[{timestamp}] Render request: {request.type} {request.width}x{request.height}"
    )

    try:
        timings: dict[str, float] = {}
        t_total0 = time.perf_counter()

        t0 = time.perf_counter()
        async with browser_pool.acquire_page() as page:
            timings["acquire_page"] = (time.perf_counter() - t0) * 1000

            # 1. Setup asset interception
            t0 = time.perf_counter()
            if request.assets:
                for pattern, local_path in request.assets.items():

                    def create_handler(path):
                        async def handle_route(route):
                            try:
                                await route.fulfill(
                                    path=path,
                                    headers={
                                        "Access-Control-Allow-Origin": "*",
                                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                                        "Access-Control-Allow-Headers": "*",
                                    },
                                )
                            except Exception as e:
                                logger.error(f"Failed to fulfill route for {path}: {e}")
                                await route.abort()

                        return handle_route

                    await page.route(pattern, create_handler(local_path))
            timings["asset_routes"] = (time.perf_counter() - t0) * 1000

            # 2. Set viewport size
            t0 = time.perf_counter()
            await page.set_viewport_size(
                {"width": request.width, "height": request.height}
            )
            timings["set_viewport"] = (time.perf_counter() - t0) * 1000

            # 3. Load content
            t0 = time.perf_counter()
            html_content = (
                request.html
                if request.html
                else f'<html><body style="margin:0;padding:0;">{request.svg}</body></html>'
            )
            payload_kb = len(html_content.encode("utf-8")) / 1024
            await page.set_content(html_content)
            timings["set_content"] = (time.perf_counter() - t0) * 1000

            # 4. Wait for assets/scripts to finish
            t0 = time.perf_counter()
            wait_until = "networkidle" if request.assets else "domcontentloaded"
            await page.wait_for_load_state(wait_until)
            timings["wait_load"] = (time.perf_counter() - t0) * 1000

            # 5. Execute Render
            t0 = time.perf_counter()
            if request.type == "png":
                buffer = await page.screenshot(full_page=True, omit_background=True)
                content_type = "image/png"
            elif request.type == "pdf":
                buffer = await page.pdf(
                    width=f"{request.width}px",
                    height=f"{request.height}px",
                    print_background=True,
                    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                )
                content_type = "application/pdf"
            elif request.type == "svg_fragment":
                fragment = await page.eval_on_selector("#globe", "el => el.innerHTML")
                buffer = fragment.encode("utf-8")
                content_type = "text/plain"
            else:
                raise HTTPException(status_code=400, detail="Invalid render type")
            timings["render"] = (time.perf_counter() - t0) * 1000

        timings["total"] = (time.perf_counter() - t_total0) * 1000
        timings_str = " ".join(f"{k}={v:.1f}ms" for k, v in timings.items())
        logger.info(
            f"render {request.type} {request.width}x{request.height} "
            f"payload={payload_kb:.1f}KB {timings_str}"
        )

        headers = {f"X-Render-{k}-Ms": f"{v:.2f}" for k, v in timings.items()}
        headers["X-Render-Payload-Kb"] = f"{payload_kb:.2f}"
        return Response(content=buffer, media_type=content_type, headers=headers)

    except Exception as err:
        logger.error(f"Render error: {err}")
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/health")
async def health_check():
    if not browser_pool.is_healthy:
        raise HTTPException(status_code=503, detail="browser not connected")
    return {"status": "ok", "pool": browser_pool.stats}


@app.get("/stats")
async def pool_stats():
    return browser_pool.stats


def create_server(host: str = "localhost", port: int = 4000, log_level: str = "info"):
    """
    Factory function required by svan2d.cli.playwright_server_commands.
    """
    import uvicorn

    config = uvicorn.Config(
        app, host=host, port=port, log_level=log_level, loop="asyncio"
    )
    return uvicorn.Server(config)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=4000, log_level="info")
