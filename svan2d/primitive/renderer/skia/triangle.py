"""Skia renderer for TriangleState — faithful mirror of TriangleRenderer."""

from __future__ import annotations

import math

from svan2d.primitive.renderer.skia._common import _fill_stroke_poly
from svan2d.primitive.state.triangle import TriangleState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class TriangleSkiaRenderer(SkiaRenderer):
    """Mirror of TriangleRenderer: equilateral triangle pointing up.

    Points: top (0,-size), bottom-left (-size*sqrt3/2, size/2),
    bottom-right (size*sqrt3/2, size/2).
    """

    def draw_core(self, canvas, state: TriangleState, ctx: SkiaContext) -> None:
        h = state.size
        w = state.size * math.sqrt(3) / 2
        pts = [(0.0, -h), (-w, h / 2), (w, h / 2)]
        _fill_stroke_poly(self, canvas, state, pts)
