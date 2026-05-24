"""Raster converter that renders via the Skia canvas backend (bypassing SVG).

Opt-in (ConverterType.SKIA). Outputs PNG or WebP (no PDF). The Skia backend
renders a scene only if it can render it completely. Before drawing, the scene
is validated once; if any primitive or feature is unsupported, conversion stops
with a detailed error listing exactly what Skia cannot render. There is no
fallback here — choosing a different converter is the caller's decision.

WebP quality: None encodes lossless (Skia maps quality 100 to lossless VP8L);
an int 0–100 encodes lossy at that quality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import skia

from svan2d.converter.svg_converter import SVGConverter
from svan2d.core.logger import get_logger
from svan2d.skia.base import SkiaUnsupported
from svan2d.skia.scene import render_scene_to_image
from svan2d.skia.support import check_scene

if TYPE_CHECKING:
    from svan2d.vscene.vscene import VScene

logger = get_logger()


class SkiaSvgConverter(SVGConverter):
    """Render scenes to PNG with Skia; stop with a detailed error if unsupported."""

    def __init__(self) -> None:
        super().__init__()
        self._validated_scene_id: int | None = None

    def _ensure_supported(self, scene: "VScene") -> None:
        """Validate the scene once per instance. Raises SkiaUnsupported with detail."""
        if self._validated_scene_id == id(scene):
            return
        reasons = check_scene(scene)
        if reasons:
            raise SkiaUnsupported(
                "Skia backend cannot render this scene. Unsupported:\n  - "
                + "\n  - ".join(reasons)
            )
        self._validated_scene_id = id(scene)

    def _convert_to_png(
        self,
        scene: "VScene",
        output_file: str,
        frame_time: float | None = 0.0,
        width_px: int | None = None,
        height_px: int | None = None,
    ) -> dict:
        assert width_px is not None and height_px is not None
        self._ensure_supported(scene)
        image = render_scene_to_image(scene, frame_time or 0.0, width_px, height_px)
        with open(output_file, "wb") as f:
            f.write(bytes(image.encodeToData(skia.kPNG, 100)))
        return {"success": True, "output": output_file}

    def _convert_to_webp(
        self,
        scene: "VScene",
        output_file: str,
        frame_time: float | None = 0.0,
        width_px: int | None = None,
        height_px: int | None = None,
        quality: int | None = None,
    ) -> dict:
        assert width_px is not None and height_px is not None
        self._ensure_supported(scene)
        image = render_scene_to_image(scene, frame_time or 0.0, width_px, height_px)
        # Skia maps WebP quality 100 to lossless (VP8L); None means lossless.
        webp_quality = 100 if quality is None else quality
        with open(output_file, "wb") as f:
            f.write(bytes(image.encodeToData(skia.kWEBP, webp_quality)))
        return {"success": True, "output": output_file}

    def _convert_to_pdf(
        self,
        scene: "VScene",
        output_file: str,
        frame_time: float | None = 0.0,
        inch_width: int | None = None,
        inch_height: int | None = None,
    ) -> dict:
        return {
            "success": False,
            "error": "SkiaSvgConverter renders PNG only (no PDF).",
        }
