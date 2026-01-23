from __future__ import annotations

import subprocess
import tempfile
from typing import TYPE_CHECKING, Optional

from svan2d.converter.svg_converter import SVGConverter
from svan2d.vscene.vscene import VScene

if TYPE_CHECKING:
    from svan2d.vscene.vscene import VScene


class ImageMagickSvgConverter(SVGConverter):
    """
    SVGConverter implementation using ImageMagick (convert command) for conversions.

    Requires ImageMagick to be installed on the system.
    Works with both ImageMagick 6 (convert) and ImageMagick 7 (magick convert).
    """

    def __init__(self, use_magick_prefix: bool = False):
        """
        Initialize the ImageMagick converter.

        Args:
            use_magick_prefix: If True, uses 'magick convert' (ImageMagick 7).
                             If False, uses 'convert' (ImageMagick 6).
        """
        super().__init__()
        self.use_magick_prefix = use_magick_prefix

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
        # ImageMagick uses 72 DPI as default for PDF
        width_px = int(inch_width * 72)
        height_px = int(inch_height * 72)
        return self._convert_imagemagick(
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
        return self._convert_imagemagick(
            scene, output_file, frame_time or 0.0, width_px, height_px, mode="png"
        )

    def _convert_imagemagick(
        self,
        scene: VScene,
        output_file: str,
        frame_time: float,
        width: int,
        height: int,
        mode: str,
    ) -> dict:
        """Internal helper for ImageMagick-based conversions."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=True) as tmp:
                self._get_write_scaled_svg_content(
                    scene, frame_time, width, height, tmp.name, False
                )

                # Build ImageMagick command
                if self.use_magick_prefix:
                    cmd = ["magick", "convert"]
                else:
                    cmd = ["convert"]

                cmd.extend(
                    [
                        tmp.name,
                        "-background",
                        "white",
                        "-flatten",  # Flatten layers to ensure white background
                        "-resize",
                        f"{width}x{height}!",  # Force exact dimensions
                        "-density",
                        "300",  # High quality rendering
                    ]
                )

                # Format-specific options
                if mode == "pdf":
                    cmd.extend(
                        [
                            "-units",
                            "PixelsPerInch",
                            "-page",
                            f"{width}x{height}",
                        ]
                    )
                elif mode == "png":
                    cmd.extend(
                        [
                            "-quality",
                            "95",  # High quality PNG
                        ]
                    )
                else:
                    raise ValueError(f"Unsupported mode: {mode}")

                cmd.append(output_file)

                # Execute ImageMagick
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            return {"success": True, "output": output_file}

        except subprocess.CalledProcessError as e:
            error_msg = f"ImageMagick conversion failed: {e.stderr}"
            return {"success": False, "error": error_msg}
        except FileNotFoundError:
            error_msg = (
                "ImageMagick not found. Please install ImageMagick:\n"
                "  - Ubuntu/Debian: sudo apt-get install imagemagick\n"
                "  - macOS: brew install imagemagick\n"
                "  - Windows: Download from https://imagemagick.org/script/download.php"
            )
            return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": str(e)}

