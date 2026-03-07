"""Export orchestration for the development server."""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from collections.abc import Callable

from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import get_logger
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

from . import media_encoder
from .export_job_manager import ExportJobManager, ExportStatus

logger = get_logger()


class ExportService:
    """Orchestrates single and batch export operations."""

    def __init__(self, export_manager: ExportJobManager):
        self.export_manager = export_manager

    def _make_progress_callback(self, job_id: str) -> Callable[[int, int], None]:
        """Create a progress callback for frame generation.

        Args:
            job_id: The export job ID to update.

        Returns:
            Callback that updates job progress.
        """

        def callback(frame_num: int, total: int) -> None:
            progress = frame_num / total
            self.export_manager.update_job(
                job_id,
                progress=progress,
                message=f"Generating frames {frame_num}/{total}",
            )

        return callback

    async def run_mp4_export(
        self,
        scene: VScene,
        job_id: str,
        total_frames: int,
        fps: int,
        width_px: int | None,
    ) -> None:
        """Run MP4 export in background."""
        try:
            exporter = VSceneExporter(
                scene=scene,
                output_dir=str(self.export_manager.output_dir),
                converter=ConverterType.PLAYWRIGHT_HTTP,
            )

            progress_callback = self._make_progress_callback(job_id)

            def export_func():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return exporter.to_mp4(
                    filename=f"animation_{timestamp}",
                    total_frames=total_frames,
                    framerate=fps,
                    png_width_px=width_px,
                    progress_callback=progress_callback,
                )

            await self.export_manager.run_export_job(job_id, export_func)

        except Exception as e:
            logger.error(f"MP4 export failed: {e}")
            self.export_manager.update_job(job_id, error=str(e))

    async def run_gif_export(
        self,
        scene: VScene,
        job_id: str,
        total_frames: int,
        fps: int,
        width_px: int | None,
    ) -> None:
        """Run GIF export in background."""
        try:
            exporter = VSceneExporter(
                scene=scene,
                output_dir=str(self.export_manager.output_dir),
                converter=ConverterType.PLAYWRIGHT_HTTP,
            )

            progress_callback = self._make_progress_callback(job_id)

            def export_func():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return exporter.to_gif(
                    filename=f"animation_{timestamp}",
                    total_frames=total_frames,
                    framerate=fps,
                    png_width_px=width_px,
                    progress_callback=progress_callback,
                )

            await self.export_manager.run_export_job(job_id, export_func)

        except Exception as e:
            logger.error(f"GIF export failed: {e}")
            self.export_manager.update_job(job_id, error=str(e))

    async def run_html_export(
        self,
        scene: VScene,
        job_id: str,
        total_frames: int,
        fps: int,
        interactive: bool = True,
    ) -> None:
        """Run HTML export in background."""
        try:
            exporter = VSceneExporter(
                scene=scene,
                output_dir=str(self.export_manager.output_dir),
            )

            def export_func():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                mode_suffix = "interactive" if interactive else "animation"
                return exporter.to_html(
                    filename=f"animation_{timestamp}_{mode_suffix}",
                    total_frames=total_frames,
                    framerate=fps,
                    interactive=interactive,
                )

            await self.export_manager.run_export_job(job_id, export_func)

        except Exception as e:
            logger.error(f"HTML export failed: {e}")
            self.export_manager.update_job(job_id, error=str(e))

    async def run_batch_export(
        self,
        scene: VScene,
        formats: list[tuple[str, str]],
        total_frames: int,
        fps: int,
        width_px: int | None,
        html_interactive: bool = True,
    ) -> None:
        """Run batch export with frame reuse optimization.

        Args:
            scene: The VScene to export.
            formats: List of (format_name, job_id) tuples.
            total_frames: Total number of frames to render.
            fps: Frames per second.
            width_px: Optional output width in pixels.
            html_interactive: Whether to generate interactive HTML export.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        frames_dir = Path("")
        temp_context = None

        try:
            # Update all jobs to processing
            for _, job_id in formats:
                self.export_manager.update_job(
                    job_id,
                    status=ExportStatus.PROCESSING,
                    message="Starting batch export...",
                )

            needs_frames = any(fmt[0] in ["mp4", "gif"] for fmt in formats)

            if needs_frames:
                temp_context = tempfile.TemporaryDirectory(
                    prefix="svan2d_batch_frames_"
                )
                frames_dir = Path(temp_context.name)

                logger.info(
                    f"Generating {total_frames} frames once for "
                    f"{len(formats)} format(s)..."
                )

                exporter = VSceneExporter(
                    scene=scene,
                    output_dir=str(self.export_manager.output_dir),
                    converter=ConverterType.PLAYWRIGHT_HTTP,
                )

                def batch_progress_callback(frame_num: int, total: int) -> None:
                    progress = (frame_num / total) * 0.5
                    for _, job_id in formats:
                        self.export_manager.update_job(
                            job_id,
                            progress=progress,
                            message=f"Generating frames {frame_num}/{total}",
                        )

                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    self._generate_frames_for_batch,
                    exporter,
                    frames_dir,
                    total_frames,
                    fps,
                    width_px,
                    batch_progress_callback,
                )
            else:
                loop = asyncio.get_running_loop()

            # Create each format from the shared frames
            for idx, (format_name, job_id) in enumerate(formats):
                format_progress_start = 0.5 + (idx / len(formats)) * 0.5
                format_progress_end = 0.5 + ((idx + 1) / len(formats)) * 0.5

                try:
                    if format_name == "mp4":
                        await self._create_mp4_from_frames(
                            job_id,
                            frames_dir,
                            total_frames,
                            fps,
                            timestamp,
                            format_progress_start,
                            format_progress_end,
                        )
                    elif format_name == "gif":
                        await self._create_gif_from_frames(
                            job_id,
                            frames_dir,
                            total_frames,
                            fps,
                            timestamp,
                            format_progress_start,
                            format_progress_end,
                        )
                    elif format_name.startswith("html-"):
                        interactive = "interactive" in format_name
                        embeddable = "embed" in format_name
                        await loop.run_in_executor(
                            None,
                            self._create_html_export,
                            scene,
                            job_id,
                            total_frames,
                            fps,
                            interactive,
                            embeddable,
                            timestamp,
                        )
                        self.export_manager.update_job(
                            job_id,
                            status=ExportStatus.COMPLETE,
                            progress=1.0,
                            message="Export complete",
                        )
                except Exception as e:
                    logger.error(f"{format_name.upper()} export failed: {e}")
                    self.export_manager.update_job(job_id, error=str(e))

        except Exception as e:
            logger.error(f"Batch export failed: {e}")
            for _, job_id in formats:
                job = self.export_manager.get_job(job_id)
                if job and job.status == ExportStatus.PROCESSING:
                    self.export_manager.update_job(job_id, error=str(e))

        finally:
            if temp_context:
                temp_context.cleanup()

    def _generate_frames_for_batch(
        self,
        exporter: VSceneExporter,
        frames_dir: Path,
        total_frames: int,
        fps: int,
        width_px: int | None,
        progress_callback: Callable,
    ) -> None:
        """Generate PNG frames for batch export (runs in thread pool)."""
        for frame_num, t in exporter.to_frames(
            output_dir=str(frames_dir),
            filename_pattern="frame_{:04d}",
            total_frames=total_frames,
            format="png",
            png_width_px=width_px,
            cleanup_svg_after_png_conversion=True,
            progress_callback=progress_callback,
        ):
            pass

    async def _create_mp4_from_frames(
        self,
        job_id: str,
        frames_dir: Path,
        total_frames: int,
        fps: int,
        timestamp: str,
        progress_start: float,
        progress_end: float,
    ) -> None:
        """Create MP4 from existing PNG frames."""
        self.export_manager.update_job(
            job_id, progress=progress_start, message="Encoding MP4..."
        )

        output_path = self.export_manager.output_dir / f"animation_{timestamp}.mp4"

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, media_encoder.encode_mp4, frames_dir, output_path, fps
        )

        self.export_manager.update_job(
            job_id,
            status=ExportStatus.COMPLETE,
            progress=1.0,
            output_file=output_path,
            message="Export complete",
        )

    async def _create_gif_from_frames(
        self,
        job_id: str,
        frames_dir: Path,
        total_frames: int,
        fps: int,
        timestamp: str,
        progress_start: float,
        progress_end: float,
    ) -> None:
        """Create GIF from existing PNG frames."""
        self.export_manager.update_job(
            job_id, progress=progress_start, message="Creating GIF..."
        )

        output_path = self.export_manager.output_dir / f"animation_{timestamp}.gif"

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            media_encoder.encode_gif,
            frames_dir,
            output_path,
            total_frames,
            fps,
        )

        self.export_manager.update_job(
            job_id,
            status=ExportStatus.COMPLETE,
            progress=1.0,
            output_file=output_path,
            message="Export complete",
        )

    def _create_html_export(
        self,
        scene: VScene,
        job_id: str,
        total_frames: int,
        fps: int,
        interactive: bool,
        embeddable: bool,
        timestamp: str,
    ) -> None:
        """Create HTML export (runs in thread pool)."""
        exporter = VSceneExporter(
            scene=scene,
            output_dir=str(self.export_manager.output_dir),
        )

        mode_suffix = "interactive" if interactive else "animation"
        embed_suffix = "_embed" if embeddable else ""
        output_file = exporter.to_html(
            filename=f"animation_{timestamp}_{mode_suffix}{embed_suffix}",
            total_frames=total_frames,
            framerate=fps,
            interactive=interactive,
            embeddable=embeddable,
        )

        self.export_manager.update_job(job_id, output_file=Path(output_file))
