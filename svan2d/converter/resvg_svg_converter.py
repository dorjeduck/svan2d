from __future__ import annotations

from typing import TYPE_CHECKING

from svan2d.converter.svg_converter import SVGConverter
from svan2d.core.logger import get_logger

if TYPE_CHECKING:
    from svan2d.vscene.vscene import VScene

logger = get_logger()


class ResvgSvgConverter(SVGConverter):
    """SVGConverter implementation using the Rust `resvg` library via `resvg-py`.

    PNG only. PDF is not supported by resvg; use Cairo or Playwright for PDF.

    Custom fonts can be supplied via `font_files` (explicit paths) or
    `font_dirs` (scanned for font files). Both lists are passed through to
    resvg's fontdb. By default, system fonts are also scanned; pass
    `skip_system_fonts=True` to render with only the supplied fonts.
    """

    def __init__(
        self,
        font_files: list[str] | None = None,
        font_dirs: list[str] | None = None,
        skip_system_fonts: bool = False,
    ) -> None:
        super().__init__()
        self.font_files = font_files
        self.font_dirs = font_dirs
        self.skip_system_fonts = skip_system_fonts

    def _convert_to_png(
        self,
        scene: VScene,
        output_file: str,
        frame_time: float | None = 0.0,
        width_px: int | None = None,
        height_px: int | None = None,
    ) -> dict:
        assert width_px is not None and height_px is not None
        try:
            svg_content = self._get_write_scaled_svg_content(
                scene, frame_time or 0.0, width_px, height_px, log=False
            )
            png_bytes = self._render(svg_content, width_px, height_px)
            with open(output_file, "wb") as f:
                f.write(png_bytes)
            return {"success": True, "output": output_file}
        except Exception as e:
            logger.error(f"ResvgSvgConverter PNG error: {e}")
            return {"success": False, "error": str(e)}

    def _convert_to_pdf(
        self,
        scene: VScene,
        output_file: str,
        frame_time: float | None = 0.0,
        inch_width: int | None = None,
        inch_height: int | None = None,
    ) -> dict:
        return {
            "success": False,
            "error": "ResvgSvgConverter does not support PDF; use Cairo or Playwright.",
        }

    def render_svg_to_png(
        self,
        svg_content: str,
        output_path: str,
        width: int,
        height: int,
    ) -> bool:
        try:
            png_bytes = self._render(svg_content, width, height)
            with open(output_path, "wb") as f:
                f.write(png_bytes)
            return True
        except Exception as e:
            logger.error(f"ResvgSvgConverter render error: {e}")
            return False

    def _render(self, svg_content: str, width: int, height: int) -> bytes:
        import resvg_py

        return resvg_py.svg_to_bytes(
            svg_string=svg_content,
            width=width,
            height=height,
            font_files=self.font_files,
            font_dirs=self.font_dirs,
            skip_system_fonts=self.skip_system_fonts,
        )
