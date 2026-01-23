from __future__ import annotations

import subprocess
import tempfile
from typing import TYPE_CHECKING, Optional

from svan2d.converter.svg_converter import SVGConverter
from svan2d.vscene.vscene import VScene

if TYPE_CHECKING:
    from svan2d.vscene.vscene import VScene


class InkscapeSvgConverter(SVGConverter):
    """
    SVGConverter implementation using Inkscape CLI for conversions.
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
        width_px = int(inch_width * 96)
        height_px = int(inch_height * 96)
        return self._convert_inkscape(
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
        return self._convert_inkscape(
            scene, output_file, frame_time or 0.0, width_px, height_px, mode="png"
        )

    def _convert_inkscape(
        self,
        scene: VScene,
        output_file: str,
        frame_time: float,
        width: int,
        height: int,
        mode: str,
    ) -> dict:
        """Internal helper for Inkscape-based conversions."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=True) as tmp:
                self._get_write_scaled_svg_content(
                    scene, frame_time, width, height, tmp.name, False
                )

                cmd = [
                    "inkscape",
                    tmp.name,
                    f"--export-type={mode}",
                    f"--export-width={int(width)}",
                    f"--export-height={int(height)}",
                    f"--export-filename={output_file}",
                ]

                subprocess.run(cmd, check=True)

            return {"success": True, "output": output_file}

        except Exception as e:
            return {"success": False, "error": str(e)}
