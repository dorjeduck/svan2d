"""Skia renderer for CircleState — faithful mirror of CircleRenderer."""

from __future__ import annotations

import skia

from svan2d.primitive.renderer.skia._common import _parse_dash
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
            if state.stroke_dasharray:
                intervals = _parse_dash(state.stroke_dasharray)
                if intervals:
                    stroke.setPathEffect(skia.DashPathEffect.Make(intervals, 0.0))
            canvas.drawCircle(0, 0, state.radius, stroke)
