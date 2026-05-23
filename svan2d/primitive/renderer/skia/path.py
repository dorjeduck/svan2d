"""Skia renderer for PathState — faithful mirror of PathRenderer."""

from __future__ import annotations

import skia

from svan2d.path.svg_path import SVGPath
from svan2d.primitive.renderer.skia._common import (
    _CAP,
    _JOIN,
    _parse_dash,
    _svgpath_to_skia,
)
from svan2d.primitive.state.path import PathState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class PathSkiaRenderer(SkiaRenderer):
    """Mirror of PathRenderer: an SVG path (`d`), fill-rule, dash, draw_commands/progress.

    Geometry is taken from svan2d's own SVGPath.to_cubic_beziers() (the canonical
    normalization) and mapped to skia path ops, so curves match exactly.
    """

    def draw_core(self, canvas, state: PathState, ctx: SkiaContext) -> None:
        svg_path = state.data if isinstance(state.data, SVGPath) else SVGPath.from_string(str(state.data))

        # draw_commands: render only the first N commands (parameter-based).
        draw_commands = state.draw_commands
        if draw_commands < 1.0:
            n = max(int(draw_commands * len(svg_path.commands)), 1)
            svg_path = SVGPath(svg_path.commands[:n])

        path = _svgpath_to_skia(svg_path)
        path.setFillType(
            skia.PathFillType.kEvenOdd
            if str(state.fill_rule) == "evenodd"
            else skia.PathFillType.kWinding
        )

        fill = self.fill_paint(state)
        if fill is not None:
            canvas.drawPath(path, fill)

        stroke = self.stroke_paint(state)
        if stroke is not None:
            stroke.setStrokeCap(_CAP.get(state.stroke_linecap or "", skia.Paint.kButt_Cap))
            stroke.setStrokeJoin(_JOIN.get(state.stroke_linejoin or "", skia.Paint.kMiter_Join))
            effect = self._dash_effect(state, svg_path, draw_commands)
            if effect is not None:
                stroke.setPathEffect(effect)
            canvas.drawPath(path, stroke)

    @staticmethod
    def _dash_effect(state: PathState, svg_path: SVGPath, draw_commands: float):
        # draw_progress (arc-length) takes effect only when draw_commands is inactive,
        # matching PathRenderer.
        if state.draw_progress < 1.0 and draw_commands >= 1.0 and state.stroke_width > 0:
            total = svg_path.length()
            return skia.DashPathEffect.Make([total * state.draw_progress, total], 0.0)
        if state.stroke_dasharray:
            intervals = _parse_dash(state.stroke_dasharray)
            if intervals:
                return skia.DashPathEffect.Make(intervals, 0.0)
        return None
