"""Skia renderer for CircleTextState — text laid out along a circular path.

Mirror of CircleTextRenderer. That renderer builds a circular path (looping
twice so text is never clipped) and places text along it via SVG <textPath>;
here the same path is walked with a skia.PathMeasure and each glyph is drawn
with drawString, rotated to the path tangent — the technique used by
PathTextSkiaRenderer. The offset-to-distance mapping mirrors
CircleTextRenderer._create_text_element exactly.
"""

from __future__ import annotations

import skia

from svan2d.path.svg_path import SVGPath
from svan2d.primitive.renderer.circle_text import _angle_fraction
from svan2d.primitive.renderer.skia._common import _svgpath_to_skia, draw_along_path
from svan2d.primitive.state.circle_text import CircleTextState
from svan2d.skia.base import SkiaContext, SkiaRenderer, smooth_font


class CircleTextSkiaRenderer(SkiaRenderer):
    """Mirror of CircleTextRenderer: system-font glyphs placed around a circle."""

    def draw_core(self, canvas, state: CircleTextState, ctx: SkiaContext) -> None:
        fill = self.fill_paint(state)
        if fill is None or not state.text:
            return

        path = _svgpath_to_skia(SVGPath.from_string(self._circle_path(state)))
        pm = skia.PathMeasure(path, False)
        length = pm.getLength()
        if length <= 0:
            return

        font = smooth_font(
            ctx.typeface(state.font_family, state.font_weight), state.font_size
        )

        if isinstance(state.text, list):
            texts = state.text
            num = len(texts)
            if state.angles is not None and len(state.angles) < num:
                raise ValueError(
                    f"Length of angles ({len(state.angles)}) must be equal or bigger "
                    f"than number of texts ({num})"
                )
            # `rotation` is not added here: the element's transform already
            # turns the whole circle by it.
            for i, content in enumerate(texts):
                if state.angles is not None:
                    # Cartesian degrees (0=East, CCW) -> path fraction.
                    position = _angle_fraction(state.angles[i], state.text_facing_inward)
                else:
                    position = i / num
                self._draw_text(canvas, str(content), position, pm, length, font, fill, state, ctx)
        else:
            self._draw_text(canvas, str(state.text), 0.0, pm, length, font, fill, state, ctx)

    @staticmethod
    def _circle_path(state: CircleTextState) -> str:
        """Same double-loop arc path CircleTextRenderer._create_circle_path builds."""
        r = state.radius
        d = "1" if state.text_facing_inward else "0"
        return (
            f"M 0,{r} "
            f"A {r},{r} 0 0,{d} 0,{-r} "
            f"A {r},{r} 0 0,{d} 0,{r} "
            f"A {r},{r} 0 0,{d} 0,{-r} "
            f"A {r},{r} 0 0,{d} 0,{r}"
        )

    def _draw_text(self, canvas, text, offset, pm, length, font, paint, state, ctx) -> None:
        # CircleTextRenderer maps the 0-1 offset onto the middle of the double loop.
        mapped = 0.25 + offset * 0.5
        baseline = self._baseline_offset(font.getMetrics(), state.dominant_baseline)
        draw_along_path(canvas, text, mapped * length, pm, font, paint,
                        state.letter_spacing or 0, state.text_anchor, baseline, ctx)

    @staticmethod
    def _baseline_offset(metrics, baseline: str) -> float:
        if baseline in ("central", "middle"):
            return -(metrics.fAscent + metrics.fDescent) / 2
        if baseline == "hanging":
            return -metrics.fAscent
        return 0.0  # alphabetic / auto
