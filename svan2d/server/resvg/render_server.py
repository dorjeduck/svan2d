"""FastAPI-based rendering server using `resvg-py`.

Mirrors the shape of the playwright_http server: POST /render with svg + width
+ height, returns PNG bytes. PNG only — resvg does not produce PDF.

resvg-py rebuilds its fontdb on every call, so this server does not save
fontdb cost — only the per-process Python interpreter + import startup.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Literal

import resvg_py
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from svan2d.core.logger import get_logger

logger = get_logger()


class RenderRequest(BaseModel):
    """Request model for /render endpoint."""

    svg: str
    type: Literal["png"] = "png"
    width: int
    height: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Resvg render server starting")
    yield
    logger.info("Resvg render server stopping")


app = FastAPI(
    title="Svan2D Resvg Render Server",
    description="HTTP server for rendering SVG using resvg-py",
    version="1.0.0",
    lifespan=lifespan,
)


def _render_sync(svg: str, width: int, height: int) -> bytes:
    return resvg_py.svg_to_bytes(svg_string=svg, width=width, height=height)


@app.post("/render")
async def render(request: RenderRequest) -> Response:
    if request.type != "png":
        raise HTTPException(
            status_code=400, detail="resvg server supports png only"
        )

    timings: dict[str, float] = {}
    t_total0 = time.perf_counter()
    payload_kb = len(request.svg.encode("utf-8")) / 1024

    try:
        t0 = time.perf_counter()
        png_bytes = await run_in_threadpool(
            _render_sync, request.svg, request.width, request.height
        )
        timings["render"] = (time.perf_counter() - t0) * 1000
        timings["total"] = (time.perf_counter() - t_total0) * 1000

        timings_str = " ".join(f"{k}={v:.1f}ms" for k, v in timings.items())
        logger.info(
            f"render png {request.width}x{request.height} "
            f"payload={payload_kb:.1f}KB {timings_str}"
        )

        headers = {f"X-Render-{k}-Ms": f"{v:.2f}" for k, v in timings.items()}
        headers["X-Render-Payload-Kb"] = f"{payload_kb:.2f}"
        return Response(content=png_bytes, media_type="image/png", headers=headers)

    except Exception as err:
        logger.error(f"Resvg render error: {err}")
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/health")
async def health_check():
    return {"status": "ok", "resvg_version": resvg_py.__resvg_version__}


def create_server(host: str = "localhost", port: int = 4100, log_level: str = "info"):
    """Factory for uvicorn.Server, parallel to playwright's create_server."""
    import uvicorn

    config = uvicorn.Config(
        app, host=host, port=port, log_level=log_level, loop="asyncio"
    )
    return uvicorn.Server(config)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=4100, log_level="info")
