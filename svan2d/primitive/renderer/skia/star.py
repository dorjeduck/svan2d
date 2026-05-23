"""Skia renderer for StarState — faithful mirror of StarRenderer."""

from __future__ import annotations

import math

from svan2d.primitive.renderer.skia._common import _fill_stroke_poly
from svan2d.primitive.state.star import StarState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class StarSkiaRenderer(SkiaRenderer):
    """Mirror of StarRenderer: alternating outer/inner radii from East (0deg)."""

    def draw_core(self, canvas, state: StarState, ctx: SkiaContext) -> None:
        num_points = max(3, state.num_points_star)
        pts = []
        for i in range(num_points * 2):
            angle = (i * math.pi) / num_points
            radius = state.outer_radius if i % 2 == 0 else state.inner_radius
            pts.append((radius * math.cos(angle), -radius * math.sin(angle)))
        _fill_stroke_poly(self, canvas, state, pts)
