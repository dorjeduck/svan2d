"""Skia renderer for TextState — faithful mirror of TextRenderer."""

from __future__ import annotations

import skia

from svan2d.primitive.state.text import TextState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class TextSkiaRenderer(SkiaRenderer):
    """Mirror of TextRenderer: system-font text with anchor/baseline/spacing."""

    def draw_core(self, canvas, state: TextState, ctx: SkiaContext) -> None:
        fill = self.fill_paint(state)
        if fill is None:
            return
        font = skia.Font(ctx.typeface(state.font_family, state.font_weight), float(state.font_size))
        lines = state.text if isinstance(state.text, list) else [state.text]
        metrics = font.getMetrics()
        line_h = (metrics.fDescent - metrics.fAscent) + metrics.fLeading
        base = self._baseline_offset(metrics, state.dominant_baseline)
        if len(lines) > 1:
            base -= line_h * (len(lines) - 1) / 2
        for i, line in enumerate(lines):
            self._draw_line(canvas, str(line), base + i * line_h, font, fill, state)

    def _draw_line(self, canvas, text, y, font, paint, state: TextState) -> None:
        spacing = state.letter_spacing or 0
        if spacing:
            total = sum(font.measureText(c) + spacing for c in text) - spacing
            x = self._anchor_offset(total, state.text_anchor)
            for c in text:
                canvas.drawString(c, x, y, font, paint)
                x += font.measureText(c) + spacing
        else:
            x = self._anchor_offset(font.measureText(text), state.text_anchor)
            canvas.drawString(text, x, y, font, paint)

    @staticmethod
    def _anchor_offset(width: float, anchor: str) -> float:
        if anchor == "middle":
            return -width / 2
        if anchor == "end":
            return -width
        return 0.0  # start

    @staticmethod
    def _baseline_offset(metrics, baseline: str) -> float:
        if baseline in ("central", "middle"):
            return -(metrics.fAscent + metrics.fDescent) / 2
        if baseline == "hanging":
            return -metrics.fAscent
        return 0.0  # alphabetic / auto
