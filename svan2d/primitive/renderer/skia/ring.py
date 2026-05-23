"""Skia renderer for RingState — faithful mirror of RingRenderer."""

from __future__ import annotations

import skia

from svan2d.primitive.state.ring import RingState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class RingSkiaRenderer(SkiaRenderer):
    """Annulus drawn as two concentric circles with even-odd fill."""

    def draw_core(self, canvas, state: RingState, ctx: SkiaContext) -> None:
        path = skia.Path()
        path.setFillType(skia.PathFillType.kEvenOdd)
        path.addCircle(0.0, 0.0, state.outer_radius)
        path.addCircle(0.0, 0.0, state.inner_radius)

        fill = self.fill_paint(state)
        if fill is not None:
            canvas.drawPath(path, fill)
        stroke = self.stroke_paint(state)
        if stroke is not None:
            canvas.drawPath(path, stroke)
