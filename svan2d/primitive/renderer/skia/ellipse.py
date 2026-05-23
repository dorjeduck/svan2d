"""Skia renderer for EllipseState — faithful mirror of EllipseRenderer."""

from __future__ import annotations

import skia

from svan2d.primitive.state.ellipse import EllipseState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class EllipseSkiaRenderer(SkiaRenderer):
    """Mirror of EllipseRenderer: ellipse centered at origin, rx/ry."""

    def draw_core(self, canvas, state: EllipseState, ctx: SkiaContext) -> None:
        rect = skia.Rect.MakeLTRB(-state.rx, -state.ry, state.rx, state.ry)
        fill = self.fill_paint(state)
        if fill is not None:
            canvas.drawOval(rect, fill)
        stroke = self.stroke_paint(state)
        if stroke is not None:
            canvas.drawOval(rect, stroke)
