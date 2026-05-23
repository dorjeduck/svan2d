"""Skia base for multi-path-variant renderers — mirror of PathVariantsRenderer.

Like the drawsvg PathVariantsRenderer, subclasses define a ``PATH_VARIANTS``
dict ({variant: {"path": str | list[str], "center": (cx, cy), ...}}) and the
selected variant's path string(s) are drawn filled/stroked, translated so the
variant's center sits at the local origin. The base draw() applies the element
transform/opacity, so draw_core works in the variant's own coordinates exactly
as PathVariantsRenderer._render_core does.
"""

from __future__ import annotations

from abc import ABC
from typing import Any

from svan2d.path.svg_path import SVGPath
from svan2d.primitive.renderer.skia._common import _svgpath_to_skia
from svan2d.skia.base import SkiaContext, SkiaRenderer


class PathVariantsSkiaRenderer(SkiaRenderer, ABC):
    """Skia mirror of PathVariantsRenderer; subclasses define PATH_VARIANTS."""

    PATH_VARIANTS: dict[str, dict[str, Any]] = {}

    def __init__(self, variant: str | None = None) -> None:
        if not self.PATH_VARIANTS:
            raise NotImplementedError("Subclass must define PATH_VARIANTS dictionary")
        if variant is None:
            variant = next(iter(self.PATH_VARIANTS))
        if variant not in self.PATH_VARIANTS:
            available = list(self.PATH_VARIANTS)
            raise ValueError(f"Unknown variant '{variant}'. Available: {available}")
        self.variant = variant
        self.data = self.PATH_VARIANTS[variant]

    def draw_core(self, canvas, state, ctx: SkiaContext) -> None:
        cx, cy = self.data["center"]
        fill = self.fill_paint(state)
        stroke = self.stroke_paint(state)
        if fill is None and stroke is None:
            return

        data = self.data["path"]
        paths = data if isinstance(data, list) else [data]
        canvas.save()
        canvas.translate(-cx, -cy)
        try:
            for path_string in paths:
                path = _svgpath_to_skia(SVGPath.from_string(path_string))
                if fill is not None:
                    canvas.drawPath(path, fill)
                if stroke is not None:
                    canvas.drawPath(path, stroke)
        finally:
            canvas.restore()
