"""
FastAPI development server for live animation preview.

Provides live browser preview with hot-reload for Svan2D animations.
"""

import asyncio
from pathlib import Path

from fastapi import FastAPI

from svan2d.core.logger import get_logger
from svan2d.vscene import VScene

from .export_job_manager import ExportJobManager
from .export_service import ExportService
from .file_watcher import FileWatcher
from .module_loader import safe_reload_module
from .preview_service import PreviewService
from .routes import create_routes
from .websocket_manager import ConnectionManager

logger = get_logger()


class DevServer:
    """
    Development server for live animation preview.

    Watches a Python animation file, reloads it on changes, and broadcasts
    updates to connected browsers via WebSocket.
    """

    def __init__(
        self,
        file_path: Path,
        num_frames: int = 20,
        play_interval_ms: int = 100,
        port: int = 8000,
    ):
        self.file_path = file_path.resolve()
        self.num_frames = num_frames
        self.play_interval_ms = play_interval_ms
        self.port = port

        # Current scene state
        self.current_scene: VScene | None = None
        self.current_error: str | None = None

        # Compose services
        self.connection_manager = ConnectionManager()

        self.export_manager = ExportJobManager(
            output_dir=self.file_path.parent / "exports"
        )

        self.preview_service = PreviewService(
            connection_manager=self.connection_manager,
            num_frames=num_frames,
            play_interval_ms=play_interval_ms,
        )

        self.export_service = ExportService(
            export_manager=self.export_manager
        )

        # File watcher (initialized in start_watching)
        self.file_watcher: FileWatcher | None = None

        # Event loop (set when server starts)
        self.loop: asyncio.AbstractEventLoop | None = None

        # Create FastAPI app
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title="Svan2D Dev Server",
            description="Development server for live animation preview",
            version="0.3.0",
        )

        @app.on_event("startup")
        async def startup_event():
            self.loop = asyncio.get_running_loop()

        create_routes(app, self)

        return app

    def _on_file_changed(self) -> None:
        """Callback invoked when the animation file changes.

        Reloads the module and broadcasts the update to all clients.
        Runs in the file watcher thread, so schedules async work on the main loop.
        """
        logger.info(f"File changed: {self.file_path.name}")

        scene, error = safe_reload_module(self.file_path)

        if error:
            logger.error(f"Reload error: {error}")
            self.current_scene = None
            self.current_error = error
        else:
            logger.info(f"Reload successful: {self.file_path.name}")
            self.current_scene = scene
            self.current_error = None

        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.preview_service.send_current(
                    self.current_scene, self.current_error
                ),
                self.loop,
            )

    def start_watching(self) -> None:
        """Start watching the animation file for changes. Also performs initial load."""
        logger.info(f"Loading animation file: {self.file_path}")
        scene, error = safe_reload_module(self.file_path)

        if error:
            logger.error(f"Initial load error: {error}")
            self.current_error = error
        else:
            logger.info(f"Initial load successful: {self.file_path.name}")
            self.current_scene = scene

        self.file_watcher = FileWatcher(
            file_path=self.file_path,
            on_change_callback=self._on_file_changed,
            debounce_ms=200,
        )
        self.file_watcher.start()
        logger.info(f"Watching for changes: {self.file_path}")

    def stop_watching(self) -> None:
        """Stop watching the animation file."""
        if self.file_watcher:
            self.file_watcher.stop()
            logger.info("File watching stopped")


def create_app(
    file_path: Path,
    num_frames: int = 20,
    play_interval_ms: int = 100,
    port: int = 8000,
) -> tuple[FastAPI, DevServer]:
    """Create a development server app.

    Args:
        file_path: Path to the Python animation file.
        num_frames: Number of frames for preview.
        play_interval_ms: Playback interval in milliseconds.
        port: Server port.

    Returns:
        Tuple of (FastAPI app, DevServer instance).
    """
    dev_server = DevServer(
        file_path=file_path,
        num_frames=num_frames,
        play_interval_ms=play_interval_ms,
        port=port,
    )

    return dev_server.app, dev_server
