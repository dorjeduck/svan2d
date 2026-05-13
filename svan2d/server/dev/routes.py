"""FastAPI route definitions for the development server."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from svan2d.core.logger import get_logger

from .export_job_manager import ExportFormat

if TYPE_CHECKING:
    from fastapi import FastAPI

    from .server import DevServer

logger = get_logger()


class ExportRequest(BaseModel):
    """Request model for export operations."""

    frames: int = 60
    fps: int = 30
    width_px: int | None = None
    html_interactive: bool = True


class BatchExportRequest(BaseModel):
    """Request model for batch export operations (multiple formats)."""

    formats: list[str]
    frames: int = 60
    fps: int = 30
    width_px: int | None = None
    html_interactive: bool = True


def create_routes(app: FastAPI, server: DevServer) -> None:
    """Register all FastAPI routes on the app.

    Args:
        app: The FastAPI application.
        server: The DevServer instance providing services.
    """
    templates_dir = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))

    @app.get("/", response_class=HTMLResponse)
    async def serve_preview():
        return templates.TemplateResponse(
            "preview.html",
            {
                "request": {},
                "filename": server.file_path.name,
                "port": server.port,
            },
        )

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await server.connection_manager.connect(websocket)
        try:
            await server.preview_service.send_current(
                server.current_scene, server.current_error
            )
            while True:
                try:
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break
        except WebSocketDisconnect:
            pass
        except RuntimeError as e:
            if "not connected" in str(e).lower():
                logger.debug(
                    "WebSocket disconnected during preview generation"
                )
            else:
                raise
        finally:
            server.connection_manager.disconnect(websocket)

    @app.get("/health")
    async def health_check():
        return {
            "status": "ok",
            "service": "svan2d-devserver",
            "file": str(server.file_path),
        }

    @app.post("/export/mp4")
    async def export_mp4(request: ExportRequest):
        if not server.current_scene:
            return JSONResponse(
                {"error": "No scene loaded"}, status_code=400
            )
        job = server.export_manager.create_job(ExportFormat.MP4)
        asyncio.create_task(
            server.export_service.run_mp4_export(
                server.current_scene,
                job.job_id,
                request.frames,
                request.fps,
                request.width_px,
            )
        )
        return {"job_id": job.job_id, "status": job.status.value}

    @app.post("/export/gif")
    async def export_gif(request: ExportRequest):
        if not server.current_scene:
            return JSONResponse(
                {"error": "No scene loaded"}, status_code=400
            )
        job = server.export_manager.create_job(ExportFormat.GIF)
        asyncio.create_task(
            server.export_service.run_gif_export(
                server.current_scene,
                job.job_id,
                request.frames,
                request.fps,
                request.width_px,
            )
        )
        return {"job_id": job.job_id, "status": job.status.value}

    @app.post("/export/html")
    async def export_html(request: ExportRequest):
        if not server.current_scene:
            return JSONResponse(
                {"error": "No scene loaded"}, status_code=400
            )
        job = server.export_manager.create_job(ExportFormat.HTML)
        asyncio.create_task(
            server.export_service.run_html_export(
                server.current_scene,
                job.job_id,
                request.frames,
                request.fps,
                request.html_interactive,
            )
        )
        return {"job_id": job.job_id, "status": job.status.value}

    @app.post("/export/batch")
    async def export_batch(request: BatchExportRequest):
        if not server.current_scene:
            return JSONResponse(
                {"error": "No scene loaded"}, status_code=400
            )

        job_ids = []
        formats = []

        for format_str in request.formats:
            if format_str == "mp4":
                job = server.export_manager.create_job(ExportFormat.MP4)
                job_ids.append(job.job_id)
                formats.append(("mp4", job.job_id))
            elif format_str == "gif":
                job = server.export_manager.create_job(ExportFormat.GIF)
                job_ids.append(job.job_id)
                formats.append(("gif", job.job_id))
            elif format_str == "html-interactive":
                job_standalone = server.export_manager.create_job(
                    ExportFormat.HTML
                )
                job_embeddable = server.export_manager.create_job(
                    ExportFormat.HTML
                )
                job_ids.extend(
                    [job_standalone.job_id, job_embeddable.job_id]
                )
                formats.append(
                    ("html-interactive-standalone", job_standalone.job_id)
                )
                formats.append(
                    ("html-interactive-embed", job_embeddable.job_id)
                )
            elif format_str == "html-animation":
                job_standalone = server.export_manager.create_job(
                    ExportFormat.HTML
                )
                job_embeddable = server.export_manager.create_job(
                    ExportFormat.HTML
                )
                job_ids.extend(
                    [job_standalone.job_id, job_embeddable.job_id]
                )
                formats.append(
                    ("html-animation-standalone", job_standalone.job_id)
                )
                formats.append(
                    ("html-animation-embed", job_embeddable.job_id)
                )

        asyncio.create_task(
            server.export_service.run_batch_export(
                server.current_scene,
                formats,
                request.frames,
                request.fps,
                request.width_px,
                request.html_interactive,
            )
        )

        return {"job_ids": job_ids, "status": "queued"}

    @app.get("/export/status/{job_id}")
    async def export_status(job_id: str):
        job = server.export_manager.get_job(job_id)
        if not job:
            return JSONResponse(
                {"error": "Job not found"}, status_code=404
            )
        return job.to_dict()

    @app.post("/export/cancel/{job_id}")
    async def export_cancel(job_id: str):
        success = server.export_manager.cancel_job(job_id)
        if not success:
            return JSONResponse(
                {"error": "Job not found or already complete"},
                status_code=400,
            )
        return {"status": "cancelled"}

    @app.get("/export/download/{filename}")
    async def export_download(filename: str):
        file_path = server.export_manager.output_dir / filename
        if not file_path.exists():
            return JSONResponse(
                {"error": "File not found"}, status_code=404
            )
        return FileResponse(
            file_path,
            filename=filename,
            media_type="application/octet-stream",
        )
