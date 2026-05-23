"""Skia renderer for NumberState — faithful mirror of NumberRenderer."""

from __future__ import annotations

import skia

from svan2d.primitive.renderer.skia.text import TextSkiaRenderer
from svan2d.primitive.state.number import NumberState
from svan2d.skia.base import SkiaContext


class NumberSkiaRenderer(TextSkiaRenderer):
    """Mirror of NumberRenderer.

    Standard formats render as a single text element (handled by the base
    TextSkiaRenderer). AUTO_ALIGNED/FIXED_ALIGNED render two strings: the
    integer part right-anchored at x=0 and the decimal part left-anchored at
    x=0, keeping the decimal point fixed.
    """

    def draw_core(self, canvas, state: NumberState, ctx: SkiaContext) -> None:
        if str(state.format) in ("auto_aligned", "fixed_aligned"):
            self._draw_aligned(canvas, state, ctx)
        else:
            super().draw_core(canvas, state, ctx)

    def _draw_aligned(self, canvas, state: NumberState, ctx: SkiaContext) -> None:
        fill = self.fill_paint(state)
        if fill is None:
            return
        font = skia.Font(
            ctx.typeface(state.font_family, state.font_weight), float(state.font_size)
        )
        y = self._baseline_offset(font.getMetrics(), state.dominant_baseline)

        int_text = state.prefix + state._integer_part
        # integer part: right edge at x=0
        self._draw_at(canvas, int_text, "end", y, font, fill, state)

        dec_text = (state._decimal_part + state.suffix) if state._has_decimals else state.suffix
        if dec_text:
            # decimal part: left edge at x=0
            self._draw_at(canvas, dec_text, "start", y, font, fill, state)

    def _draw_at(self, canvas, text, anchor, y, font, paint, state: NumberState) -> None:
        spacing = state.letter_spacing or 0
        if spacing:
            total = sum(font.measureText(c) + spacing for c in text) - spacing
            x = self._anchor_offset(total, anchor)
            for c in text:
                canvas.drawString(c, x, y, font, paint)
                x += font.measureText(c) + spacing
        else:
            x = self._anchor_offset(font.measureText(text), anchor)
            canvas.drawString(text, x, y, font, paint)
