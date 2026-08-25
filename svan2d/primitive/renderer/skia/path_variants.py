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

    @classmethod
    def variant_data(cls, state) -> dict[str, Any]:
        """The entry of PATH_VARIANTS the state asks for; mirrors the SVG base."""
        if not cls.PATH_VARIANTS:
            raise NotImplementedError("Subclass must define PATH_VARIANTS dictionary")
        variant = state.variant
        if variant is None:
            return next(iter(cls.PATH_VARIANTS.values()))
        if variant not in cls.PATH_VARIANTS:
            available = list(cls.PATH_VARIANTS)
            raise ValueError(f"Unknown variant '{variant}'. Available: {available}")
        return cls.PATH_VARIANTS[variant]

    def draw_core(self, canvas, state, ctx: SkiaContext) -> None:
        variant_data = self.variant_data(state)
        cx, cy = variant_data["center"]
        fill = self.fill_paint(state)
        stroke = self.stroke_paint(state)
        if fill is None and stroke is None:
            return

        data = variant_data["path"]
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
