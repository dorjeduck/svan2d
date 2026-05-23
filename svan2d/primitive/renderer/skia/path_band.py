"""Skia renderer for PathBandState — faithful mirror of PathBandRenderer."""

from __future__ import annotations

import skia

from svan2d.primitive.renderer.skia._common import _CAP, _JOIN
from svan2d.primitive.state.path_band import PathBandState
from svan2d.skia.base import SkiaContext, SkiaRenderer, skia_color


class PathBandSkiaRenderer(SkiaRenderer):
    """One line per segment, with per-segment stroke color/opacity/width.

    Mirrors PathBandRenderer: per-segment values override the shared
    stroke_color/stroke_opacity/stroke_width. Y is negated (Y-up → Y-down).
    Gradient segments are rejected up front by the capability scan.
    """

    def draw_core(self, canvas, state: PathBandState, ctx: SkiaContext) -> None:
        cap = _CAP.get(state.stroke_linecap or "", skia.Paint.kButt_Cap)
        join = _JOIN.get(state.stroke_linejoin or "", skia.Paint.kMiter_Join)

        opacities = state.stroke_opacities
        widths = state.stroke_widths
        colors = state.stroke_colors

        for i, (a, b) in enumerate(state.segments):
            color = colors[i] if colors is not None and i < len(colors) else state.stroke_color
            if color is None or color.is_none():
                continue
            width = widths[i] if widths is not None and i < len(widths) else state.stroke_width
            if width is None or width <= 0:
                continue
            opacity = (
                opacities[i]
                if opacities is not None and i < len(opacities)
                else state.stroke_opacity
            )

            paint = skia.Paint(
                AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=float(width)
            )
            paint.setColor(skia_color(color, opacity if opacity is not None else 1.0))
            paint.setStrokeCap(cap)
            paint.setStrokeJoin(join)
            canvas.drawLine(a.x, -a.y, b.x, -b.y, paint)
