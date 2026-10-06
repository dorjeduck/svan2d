"""Skia renderer for TextState — faithful mirror of TextRenderer."""

from __future__ import annotations

import skia

from svan2d.primitive.renderer.skia._common import draw_line
from svan2d.primitive.state.text import TextState
from svan2d.skia.base import SkiaContext, SkiaRenderer, smooth_font


class TextSkiaRenderer(SkiaRenderer):
    """Mirror of TextRenderer: system-font text with anchor/baseline/spacing."""

    def draw_core(self, canvas, state: TextState, ctx: SkiaContext) -> None:
        fill = self.fill_paint(state)
        if fill is None:
            return
        font = smooth_font(ctx.typeface(state.font_family, state.font_weight), state.font_size)
        lines = state.text if isinstance(state.text, list) else [state.text]
        metrics = font.getMetrics()
        line_h = (metrics.fDescent - metrics.fAscent) + metrics.fLeading
        base = self._baseline_offset(metrics, state.dominant_baseline)
        if len(lines) > 1:
            base -= line_h * (len(lines) - 1) / 2
        for i, line in enumerate(lines):
            draw_line(canvas, str(line), 0.0, base + i * line_h, font, fill,
                      state.letter_spacing or 0, state.text_anchor, ctx)

    @staticmethod
    def _baseline_offset(metrics, baseline: str) -> float:
        if baseline in ("central", "middle"):
            return -(metrics.fAscent + metrics.fDescent) / 2
        if baseline == "hanging":
            return -metrics.fAscent
        return 0.0  # alphabetic / auto
