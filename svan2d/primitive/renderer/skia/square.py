"""Skia renderer for SquareState — faithful mirror of SquareRenderer."""

from __future__ import annotations

from svan2d.primitive.renderer.skia._common import _draw_rect
from svan2d.primitive.state.square import SquareState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class SquareSkiaRenderer(SkiaRenderer):
    """Mirror of SquareRenderer: square centered at origin, optional corner radius."""

    def draw_core(self, canvas, state: SquareState, ctx: SkiaContext) -> None:
        _draw_rect(self, canvas, state, state.size, state.size, state.corner_radius)
