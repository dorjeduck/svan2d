"""Preview generation and broadcasting for the development server."""

import asyncio
import re

from svan2d.core.logger import get_logger
from svan2d.vscene import VScene
from svan2d.vscene.preview import PreviewRenderer

from .websocket_manager import ConnectionManager

logger = get_logger()


class PreviewService:
    """Generates preview HTML from a VScene and broadcasts it to clients."""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        num_frames: int,
        play_interval_ms: int,
    ):
        self.connection_manager = connection_manager
        self.num_frames = num_frames
        self.play_interval_ms = play_interval_ms

    def generate_html(self, scene: VScene) -> str:
        """Generate preview HTML from a VScene.

        Args:
            scene: The VScene to render.

        Returns:
            HTML string containing the interactive preview.
        """
        preview_renderer = PreviewRenderer(scene)
        times = [i / (self.num_frames - 1) for i in range(self.num_frames)]

        html_obj = preview_renderer._render_navigator(
            times=times, play_interval_ms=self.play_interval_ms
        )
        html_content = html_obj.data or ""

        # Clean any html/body/head wrapper tags if present
        if any(
            tag in html_content.lower()
            for tag in ["<!doctype", "<html", "<body", "<head"]
        ):
            html_content = re.sub(
                r"<!DOCTYPE[^>]*>", "", html_content, flags=re.IGNORECASE
            )
            html_content = re.sub(
                r"</?html[^>]*>", "", html_content, flags=re.IGNORECASE
            )
            html_content = re.sub(
                r"<head>.*?</head>",
                "",
                html_content,
                flags=re.IGNORECASE | re.DOTALL,
            )
            html_content = re.sub(
                r"</?body[^>]*>", "", html_content, flags=re.IGNORECASE
            )
            logger.debug("Cleaned HTML wrapper tags from preview content")

        return html_content.strip()

    async def send_current(
        self, scene: VScene | None, error: str | None
    ) -> None:
        """Send current preview state to all connected clients.

        Args:
            scene: Current scene (may be None).
            error: Current error message (may be None).
        """
        if error:
            await self.connection_manager.send_error(error)
        elif scene:
            try:
                loop = asyncio.get_running_loop()
                html = await loop.run_in_executor(
                    None, self.generate_html, scene
                )
                await self.connection_manager.send_update(
                    html, self.num_frames
                )
            except Exception as e:
                error_msg = f"Error generating preview: {e}"
                logger.error(error_msg)
                await self.connection_manager.send_error(error_msg)
