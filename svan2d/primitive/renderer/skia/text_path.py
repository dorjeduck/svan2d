"""Skia renderer for TextPathState — faithful mirror of TextPathRenderer.

Glyphs are drawn as filled paths (not <text>), using the same glyph cache as
the SVG renderer, so the geometry matches exactly.
"""

from __future__ import annotations

import skia

from svan2d.path.svg_path import SVGPath
from svan2d.primitive.renderer.skia._common import _svgpath_to_skia
from svan2d.primitive.state.text_path import TextPathState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class TextPathSkiaRenderer(SkiaRenderer):
    """Mirror of TextPathRenderer: each glyph cached as an SVG path, drawn filled."""

    def draw_core(self, canvas, state: TextPathState, ctx: SkiaContext) -> None:
        from svan2d.font.glyph_cache import get_glyph_cache

        fill = self.fill_paint(state)
        if fill is None or not state.text:
            return

        cache = get_glyph_cache()
        font = state._get_font()
        scale = state.font_size / font["head"].unitsPerEm

        text = state.text if isinstance(state.text, str) else "".join(state.text)
        total_width = self._text_width(cache, state.font_path, text, scale, font)

        if state.text_anchor == "middle":
            anchor_offset = -total_width / 2
        elif state.text_anchor == "end":
            anchor_offset = -total_width
        else:
            anchor_offset = 0.0

        if state.dominant_baseline == "central":
            baseline_offset = state.font_size * 0.35
        elif state.dominant_baseline == "hanging":
            baseline_offset = -state.font_size * 0.8
        elif state.dominant_baseline == "middle":
            baseline_offset = state.font_size * 0.25
        else:
            baseline_offset = 0.0

        cursor_x = 0.0
        for char in text:
            if char == " ":
                try:
                    cursor_x += cache.get_glyph(state.font_path, "n", font=font).advance_width * scale
                except ValueError:
                    cursor_x += state.font_size * 0.3
                continue
            try:
                glyph = cache.get_glyph(state.font_path, char, font=font)
            except ValueError:
                continue

            if glyph.path:
                path = _svgpath_to_skia(SVGPath.from_string(glyph.path))
                path.setFillType(skia.PathFillType.kEvenOdd)
                canvas.save()
                canvas.translate(cursor_x + anchor_offset, baseline_offset)
                canvas.scale(scale, scale)
                canvas.drawPath(path, fill)
                canvas.restore()

            cursor_x += glyph.advance_width * scale

    @staticmethod
    def _text_width(cache, font_path, text, scale, font) -> float:
        width = 0.0
        for char in text:
            try:
                glyph = cache.get_glyph(font_path, "n" if char == " " else char, font=font)
                width += glyph.advance_width * scale
            except ValueError:
                if char == " ":
                    width += scale * 500
        return width
