"""Skia renderer for ArcState — faithful mirror of ArcRenderer."""

from __future__ import annotations

import math

import skia

from svan2d.primitive.renderer.skia._common import _CAP
from svan2d.primitive.state.arc import ArcState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class ArcSkiaRenderer(SkiaRenderer):
    """Circular arc drawn with skia.Path.arcTo (SVG 'A' semantics)."""

    def draw_core(self, canvas, state: ArcState, ctx: SkiaContext) -> None:
        r = state.radius
        start_rad = math.radians(state.start_angle)
        end_rad = math.radians(state.end_angle)
        # Y negated: local SVG Y-down vs user Y-up (mirrors ArcRenderer).
        start = (r * math.cos(start_rad), -r * math.sin(start_rad))
        end = (r * math.cos(end_rad), -r * math.sin(end_rad))
        large = skia.Path.ArcSize.kLarge_ArcSize if abs(end_rad - start_rad) > math.pi \
            else skia.Path.ArcSize.kSmall_ArcSize

        path = skia.Path()
        path.moveTo(*start)
        # sweep flag 1 in SVG (positive angle, Y-down) == kCW in skia.
        path.arcTo(r, r, 0.0, large, skia.PathDirection.kCW, *end)

        fill = self.fill_paint(state)
        if fill is not None:
            canvas.drawPath(path, fill)
        stroke = self.stroke_paint(state)
        if stroke is not None:
            cap = getattr(state, "stroke_linecap", "") or ""
            stroke.setStrokeCap(_CAP.get(cap, skia.Paint.kButt_Cap))
            canvas.drawPath(path, stroke)
