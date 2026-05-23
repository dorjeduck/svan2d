"""Skia renderer for CircleState — faithful mirror of CircleRenderer."""

from __future__ import annotations

from svan2d.primitive.state.circle import CircleState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class CircleSkiaRenderer(SkiaRenderer):
    """Mirror of CircleRenderer: circle centered at origin, radius=state.radius."""

    def draw_core(self, canvas, state: CircleState, ctx: SkiaContext) -> None:
        fill = self.fill_paint(state)
        if fill is not None:
            canvas.drawCircle(0, 0, state.radius, fill)
        stroke = self.stroke_paint(state)
        if stroke is not None:
            canvas.drawCircle(0, 0, state.radius, stroke)
