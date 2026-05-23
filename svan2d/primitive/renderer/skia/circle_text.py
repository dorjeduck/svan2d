"""Skia renderer for CircleTextState — text laid out along a circular path.

Mirror of CircleTextRenderer. That renderer builds a circular path (looping
twice so text is never clipped) and places text along it via SVG <textPath>;
here the same path is walked with a skia.PathMeasure and each glyph is drawn
with drawString, rotated to the path tangent — the technique used by
PathTextSkiaRenderer. The offset-to-distance mapping mirrors
CircleTextRenderer._create_text_element exactly.
"""

from __future__ import annotations

import math

import skia

from svan2d.path.svg_path import SVGPath
from svan2d.primitive.renderer.skia._common import _svgpath_to_skia
from svan2d.primitive.state.circle_text import CircleTextState
from svan2d.skia.base import SkiaContext, SkiaRenderer


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

        font = skia.Font(
            ctx.typeface(state.font_family, state.font_weight), float(state.font_size)
        )

        if isinstance(state.text, list):
            texts = state.text
            num = len(texts)
            if state.angles is not None and len(state.angles) < num:
                raise ValueError(
                    f"Length of angles ({len(state.angles)}) must be equal or bigger "
                    f"than number of texts ({num})"
                )
            for i, content in enumerate(texts):
                if state.angles is not None:
                    # Cartesian degrees (0=East, CCW) -> path fraction.
                    angle_fraction = (90 - state.angles[i]) % 360 / 360
                    position = state.rotation / 360 + angle_fraction
                else:
                    position = state.rotation / 360 + (i / num)
                self._draw_text(canvas, str(content), position, pm, length, font, fill, state)
        else:
            self._draw_text(canvas, str(state.text), state.rotation, pm, length, font, fill, state)

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

    def _draw_text(self, canvas, text, offset, pm, length, font, paint, state) -> None:
        # CircleTextRenderer maps the 0-1 offset onto the middle of the double loop.
        mapped = 0.25 + offset * 0.5
        spacing = state.letter_spacing or 0
        advances = [font.measureText(c) for c in text]
        total = sum(advances) + spacing * (len(text) - 1) if text else 0.0
        baseline = self._baseline_offset(font.getMetrics(), state.dominant_baseline)

        cursor = mapped * length + self._anchor_offset(total, state.text_anchor)
        for char, advance in zip(text, advances):
            mid = cursor + advance / 2
            if 0.0 <= mid <= length:
                pos, tan = pm.getPosTan(mid)
                angle = math.degrees(math.atan2(tan.y(), tan.x()))
                canvas.save()
                canvas.translate(pos.x(), pos.y())
                canvas.rotate(angle)
                canvas.drawString(char, -advance / 2, baseline, font, paint)
                canvas.restore()
            cursor += advance + spacing

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
