"""Skia renderer for AstroidState — faithful mirror of AstroidRenderer."""

from __future__ import annotations

import math

import skia

from svan2d.primitive.state.astroid import AstroidState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class AstroidSkiaRenderer(SkiaRenderer):
    """Cusps joined by inward-bending quadratic Beziers (SVG 'Q' semantics)."""

    def draw_core(self, canvas, state: AstroidState, ctx: SkiaContext) -> None:
        n = state.num_cusps
        # Cusp tips, 0° = East, CCW positive; Y negated for local Y-down.
        cusps = []
        for i in range(n):
            angle = math.radians(i * (360 / n))
            cusps.append((state.radius * math.cos(angle), -state.radius * math.sin(angle)))

        path = skia.Path()
        path.moveTo(*cusps[0])
        for i in range(n):
            sx, sy = cusps[i]
            ex, ey = cusps[(i + 1) % n]
            # Control point pulled toward center by curvature.
            cx = (sx + ex) / 2 * (1 - state.curvature)
            cy = (sy + ey) / 2 * (1 - state.curvature)
            path.quadTo(cx, cy, ex, ey)
        path.close()

        fill = self.fill_paint(state)
        if fill is not None:
            canvas.drawPath(path, fill)
        stroke = self.stroke_paint(state)
        if stroke is not None:
            stroke.setStrokeCap(skia.Paint.kRound_Cap)
            stroke.setStrokeJoin(skia.Paint.kRound_Join)
            canvas.drawPath(path, stroke)
