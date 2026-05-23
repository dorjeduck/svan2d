"""Skia mirror of VertexRenderer: draws a state's contours as fill + stroke.

Registered as the default for VertexState, so any vertex shape without a
dedicated Skia renderer renders from its contours — the same geometry the SVG
backend draws. Also used for morph frames, where a state carries
_aligned_contours (see svan2d.primitive.registry).
"""

from __future__ import annotations

import skia

from svan2d.primitive.renderer.skia._common import _CAP, _add_loop, _is_closed
from svan2d.primitive.state.base_vertex import VertexState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class VertexSkiaRenderer(SkiaRenderer):
    """Faithful mirror of VertexRenderer: renders a state's contours."""

    def draw_core(self, canvas, state: VertexState, ctx: SkiaContext) -> None:
        contours = state.get_contours()
        outer = contours.outer.vertices
        if not outer:
            return
        fill = self.fill_paint(state)
        if fill is not None:
            fill_path = skia.Path()
            fill_path.setFillType(skia.PathFillType.kEvenOdd)
            _add_loop(fill_path, outer, close=True)
            for hole in contours.holes:
                _add_loop(fill_path, hole.vertices, close=True)
            canvas.drawPath(fill_path, fill)
        stroke = self.stroke_paint(state)
        if stroke is not None:
            cap = getattr(state, "stroke_linecap", "") or ""
            stroke.setStrokeCap(_CAP.get(cap, skia.Paint.kButt_Cap))
            closed = _is_closed(outer)
            progress = getattr(state, "draw_progress", 1.0)
            verts = outer if progress >= 1.0 else outer[: max(int(progress * len(outer)), 1)]
            stroke_path = skia.Path()
            _add_loop(stroke_path, verts, close=closed and progress >= 1.0)
            canvas.drawPath(stroke_path, stroke)
            for hole in contours.holes:
                hp = skia.Path()
                _add_loop(hp, hole.vertices, close=True)
                canvas.drawPath(hp, stroke)
