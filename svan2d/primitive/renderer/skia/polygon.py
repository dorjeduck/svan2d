"""Skia renderer for PolygonState — faithful mirror of PolygonRenderer."""

from __future__ import annotations

import math

from svan2d.primitive.renderer.skia._common import _fill_stroke_poly
from svan2d.primitive.state.polygon import PolygonState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class PolygonSkiaRenderer(SkiaRenderer):
    """Mirror of PolygonRenderer: regular polygon corners from East (0deg)."""

    def draw_core(self, canvas, state: PolygonState, ctx: SkiaContext) -> None:
        pts = []
        for i in range(state.num_sides):
            angle = (i / state.num_sides) * 2 * math.pi
            pts.append((state.size * math.cos(angle), -state.size * math.sin(angle)))
        _fill_stroke_poly(self, canvas, state, pts)
