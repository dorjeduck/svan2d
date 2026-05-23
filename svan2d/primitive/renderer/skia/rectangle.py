"""Skia renderer for RectangleState — faithful mirror of RectangleRenderer."""

from __future__ import annotations

from svan2d.primitive.renderer.skia._common import _draw_rect
from svan2d.primitive.state.rectangle import RectangleState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class RectangleSkiaRenderer(SkiaRenderer):
    """Mirror of RectangleRenderer: rect centered at origin, optional corner radius."""

    def draw_core(self, canvas, state: RectangleState, ctx: SkiaContext) -> None:
        _draw_rect(self, canvas, state, state.width, state.height, state.corner_radius)
