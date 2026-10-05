"""Skia renderer for PathTextState — text laid out along an SVG path.

Mirror of PathTextRenderer (which uses SVG <textPath>). Skia has no <textPath>
equivalent, so each glyph is placed by hand: a skia.PathMeasure walks the path
by arc length and, for every character, yields the position and tangent at the
glyph's midpoint. The canvas is rotated to the tangent and the glyph drawn with
drawString — the technique described in
https://www.pushing-pixels.org/2022/02/10/drawing-text-on-a-path-in-compose-desktop-with-skia.html
(getPosTan instead of an RSXform TextBlob, to keep system-font rendering
identical to TextSkiaRenderer).
"""

from __future__ import annotations

import skia

from svan2d.path.svg_path import SVGPath
from svan2d.primitive.renderer.skia._common import _svgpath_to_skia, draw_along_path
from svan2d.primitive.state.path_text import PathTextState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class PathTextSkiaRenderer(SkiaRenderer):
    """Mirror of PathTextRenderer: system-font glyphs placed along state.data."""

    def draw_core(self, canvas, state: PathTextState, ctx: SkiaContext) -> None:
        fill = self.fill_paint(state)
        if fill is None or not state.text:
            return

        assert isinstance(state.data, SVGPath), "data should be SVGPath after __post_init__"
        pm = skia.PathMeasure(_svgpath_to_skia(state.data), False)
        length = pm.getLength()
        if length <= 0:
            return

        font = skia.Font(
            ctx.typeface(state.font_family, state.font_weight), float(state.font_size)
        )

        if isinstance(state.text, list):
            texts = state.text
            num = len(texts)
            if state.offsets is not None and len(state.offsets) < num:
                raise ValueError(
                    f"Length of offsets ({len(state.offsets)}) must be equal or bigger "
                    f"than number of texts ({num})"
                )
            for i, content in enumerate(texts):
                if state.offsets is not None:
                    text_offset = state.offsets[i]
                else:
                    text_offset = i / max(1, num - 1) if num > 1 else 0.0
                final_offset = (state.offset + text_offset) % 1.0
                self._draw_text(canvas, str(content), final_offset, pm, length, font, fill, state, ctx)
        else:
            self._draw_text(canvas, str(state.text), state.offset, pm, length, font, fill, state, ctx)

    def _draw_text(self, canvas, text, offset, pm, length, font, paint, state, ctx) -> None:
        baseline = self._baseline_offset(font.getMetrics(), state.dominant_baseline)
        draw_along_path(canvas, text, offset * length, pm, font, paint,
                        state.letter_spacing or 0, state.text_anchor, baseline, ctx,
                        flip=state.flip_text)

    @staticmethod
    def _baseline_offset(metrics, baseline: str) -> float:
        if baseline in ("central", "middle"):
            return -(metrics.fAscent + metrics.fDescent) / 2
        if baseline == "hanging":
            return -metrics.fAscent
        return 0.0  # alphabetic / auto
