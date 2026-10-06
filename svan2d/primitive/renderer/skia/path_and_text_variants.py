"""Skia base for path+text-variant renderers — mirror of PathAndTextVariantsRenderer.

Like the drawsvg PathAndTextVariantsRenderer, subclasses define a
``PATH_VARIANTS`` dict where each variant carries a ``path`` (str | list[str]),
a ``text`` label with ``text_position``, plus ``viewbox`` and ``center``. The
selected variant is scaled by ``state.size / viewbox`` and translated so its
center sits at the local origin, then path(s) are drawn filled/stroked and the
label is drawn as system-font text — exactly as _render_core does.
"""

from __future__ import annotations

from abc import ABC
from typing import Any

import skia

from svan2d.path.svg_path import SVGPath
from svan2d.primitive.renderer.skia._common import _svgpath_to_skia, draw_line, svg_whitespace
from svan2d.skia.base import SkiaContext, SkiaRenderer, skia_color, smooth_font


class PathAndTextVariantsSkiaRenderer(SkiaRenderer, ABC):
    """Skia mirror of PathAndTextVariantsRenderer; subclasses define PATH_VARIANTS."""

    PATH_VARIANTS: dict[str, dict[str, Any]] = {}

    @classmethod
    def variant_data(cls, state) -> dict[str, Any]:
        """The entry of PATH_VARIANTS the state asks for; mirrors the SVG base."""
        if not cls.PATH_VARIANTS:
            raise NotImplementedError("Subclass must define PATH_VARIANTS dictionary")
        variant = state.variant
        if variant is None:
            return next(iter(cls.PATH_VARIANTS.values()))
        if variant not in cls.PATH_VARIANTS:
            available = list(cls.PATH_VARIANTS)
            raise ValueError(f"Unknown variant '{variant}'. Available: {available}")
        return cls.PATH_VARIANTS[variant]

    def draw_core(self, canvas, state, ctx: SkiaContext) -> None:
        variant_data = self.variant_data(state)
        cx, cy = variant_data["center"]
        scale_factor = state.size / variant_data["viewbox"]

        canvas.save()
        canvas.scale(scale_factor, scale_factor)
        canvas.translate(-cx, -cy)
        try:
            self._draw_paths(canvas, state)
            self._draw_text(canvas, state, ctx)
        finally:
            canvas.restore()

    # ---- paths --------------------------------------------------------------

    def _draw_paths(self, canvas, state) -> None:
        # _render_core sets opacity=state.opacity on each path; the base draw()
        # applies state.opacity again, so fold it into the paint alpha here.
        fill = self._scaled(self.fill_paint(state), state.opacity)
        stroke = self._scaled(self.stroke_paint(state), state.opacity)
        if fill is None and stroke is None:
            return
        data = self.variant_data(state)["path"]
        paths = data if isinstance(data, list) else [data]
        for path_string in paths:
            path = _svgpath_to_skia(SVGPath.from_string(path_string))
            if fill is not None:
                canvas.drawPath(path, fill)
            if stroke is not None:
                canvas.drawPath(path, stroke)

    # ---- text ---------------------------------------------------------------

    def _draw_text(self, canvas, state, ctx: SkiaContext) -> None:
        variant_data = self.variant_data(state)
        text = state.text if state.text is not None else variant_data["text"]
        text = svg_whitespace(text) if text else text
        if not text:
            return
        color = state.text_color if state.text_color and not state.text_color.is_none() else state.fill_color
        if color is None or color.is_none():
            return

        text_x, text_y = variant_data["text_position"]
        font = smooth_font(
            ctx.typeface(state.font_family, state.font_weight), state.font_size
        )
        paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kFill_Style)
        paint.setColor(skia_color(color, state.fill_opacity * state.opacity))

        draw_line(canvas, text, text_x, text_y, font, paint,
                  state.letter_spacing or 0, state.text_align, ctx)

    @staticmethod
    def _scaled(paint, factor: float):
        if paint is not None and factor < 1.0:
            paint.setAlphaf(paint.getAlphaf() * factor)
        return paint
