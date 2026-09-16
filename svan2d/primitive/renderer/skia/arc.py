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
        angle_diff = end_rad - start_rad
        large = skia.Path.ArcSize.kLarge_ArcSize if abs(angle_diff) > math.pi \
            else skia.Path.ArcSize.kSmall_ArcSize
        # Y is negated, so a positive angle sweeps CCW on screen: SVG sweep flag 0 == kCCW.
        direction = skia.PathDirection.kCCW if angle_diff > 0 else skia.PathDirection.kCW

        path = skia.Path()
        path.moveTo(*start)
        if abs(angle_diff) >= 2 * math.pi:
            # Coincident endpoints make a single arc degenerate: draw two half arcs.
            mid_rad = start_rad + (math.pi if angle_diff > 0 else -math.pi)
            mid = (r * math.cos(mid_rad), -r * math.sin(mid_rad))
            small = skia.Path.ArcSize.kSmall_ArcSize
            path.arcTo(r, r, 0.0, small, direction, *mid)
            path.arcTo(r, r, 0.0, small, direction, *start)
        else:
            path.arcTo(r, r, 0.0, large, direction, *end)

        fill = self.fill_paint(state)
        if fill is not None:
            canvas.drawPath(path, fill)
        stroke = self.stroke_paint(state)
        if stroke is not None:
            cap = getattr(state, "stroke_linecap", "") or ""
            stroke.setStrokeCap(_CAP.get(cap, skia.Paint.kButt_Cap))
            canvas.drawPath(path, stroke)
