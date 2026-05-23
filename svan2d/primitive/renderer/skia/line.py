"""Skia renderer for LineState — faithful mirror of LineRenderer."""

from __future__ import annotations

import skia

from svan2d.primitive.renderer.skia._common import _CAP, _parse_dash
from svan2d.primitive.state.line import LineState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class LineSkiaRenderer(SkiaRenderer):
    """Mirror of LineRenderer: single segment from (-length/2,0) to (length/2,0)."""

    def draw_core(self, canvas, state: LineState, ctx: SkiaContext) -> None:
        stroke = self.stroke_paint(state)
        if stroke is None:
            return
        cap = state.stroke_linecap or ""
        stroke.setStrokeCap(_CAP.get(cap, skia.Paint.kButt_Cap))
        if state.stroke_dasharray:
            intervals = _parse_dash(state.stroke_dasharray)
            if intervals:
                stroke.setPathEffect(skia.DashPathEffect.Make(intervals, 0.0))
        half = state.length / 2
        canvas.drawLine(-half, 0, half, 0, stroke)
