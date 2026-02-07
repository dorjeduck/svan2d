from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING, Optional

import cairosvg

from svan2d.converter.svg_converter import SVGConverter

if TYPE_CHECKING:
    from svan2d.vscene.vscene import VScene


class CairoSvgConverter(SVGConverter):
    """
    SVGConverter implementation using cairosvg for conversions.
    """

    def _convert_to_pdf(
        self,
        scene: VScene,
        output_file: str,
        frame_time: Optional[float] = 0.0,
        inch_width: int | None = None,
        inch_height: int | None = None,
    ) -> dict:
        """Convert a VScene to PDF with page size in inches."""
        assert inch_width is not None and inch_height is not None
        # CairoSVG expects ~96 px per inch for correct physical scaling
        width_px = int(inch_width * 96)
        height_px = int(inch_height * 96)
        return self._convert_cairo(
            scene, output_file, frame_time or 0.0, width_px, height_px, mode="pdf"
        )

    def _convert_to_png(
        self,
        scene: VScene,
        output_file: str,
        frame_time: Optional[float] = 0.0,
        width_px: int | None = None,
        height_px: int | None = None,
    ) -> dict:
        """Convert a VScene to PNG with pixel dimensions."""
        assert width_px is not None and height_px is not None
        return self._convert_cairo(
            scene, output_file, frame_time or 0.0, width_px, height_px, mode="png"
        )

    def _convert_cairo(
        self,
        scene: VScene,
        output_file: str,
        frame_time: float,
        width: int,
        height: int,
        mode: str,
    ) -> dict:
        """Internal helper for Cairo-based conversions."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=True) as tmp:
                self._get_write_scaled_svg_content(
                    scene, frame_time, width, height, tmp.name, False
                )

                kwargs = {
                    "url": tmp.name,
                    "write_to": output_file,
                    "output_width": width,
                    "output_height": height,
                }

                if mode == "pdf":
                    cairosvg.svg2pdf(**kwargs)
                elif mode == "png":
                    cairosvg.svg2png(**kwargs)
                else:
                    raise ValueError(f"Unsupported mode: {mode}")

            return {"success": True, "output": output_file}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def render_svg_to_png(
        self,
        svg_content: str,
        output_path: str,
        width: int,
        height: int,
    ) -> bool:
        """Render SVG content directly to PNG using CairoSVG."""
        try:
            cairosvg.svg2png(
                bytestring=svg_content.encode("utf-8"),
                write_to=output_path,
                output_width=width,
                output_height=height,
            )
            return True
        except Exception:
            return False
