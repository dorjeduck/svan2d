"""Text path renderer - renders text as SVG paths for smooth animation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import drawsvg as dw

from .base import Renderer, _set_elem_attr

if TYPE_CHECKING:
    from ..state.text_path import TextPathState


class TextPathRenderer(Renderer):
    """Renderer that converts text to SVG paths.

    Unlike TextRenderer which uses <text> elements, this renderer
    converts each glyph to <path> elements, eliminating font hinting
    artifacts during animation/transformation.

    Uses a two-level cache (memory + disk) for glyph paths.
    """

    def _render_core(
        self, state: "TextPathState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Group:
        """Render text as a group of path elements."""
        from svan2d.font.glyph_cache import get_glyph_cache

        group = dw.Group()

        if not state.text:
            return group

        cache = get_glyph_cache()
        font = state._get_font()

        # Calculate scale from font_size
        units_per_em = font["head"].unitsPerEm
        scale = state.font_size / units_per_em

        # Get text as string
        text = state.text if isinstance(state.text, str) else "".join(state.text)

        # Calculate total width for alignment
        total_width = self._calculate_text_width(state.font_path, text, scale, cache)

        # Calculate anchor offset
        if state.text_anchor == "middle":
            anchor_offset = -total_width / 2
        elif state.text_anchor == "end":
            anchor_offset = -total_width
        else:  # start
            anchor_offset = 0

        # Calculate vertical offset based on dominant_baseline
        if state.dominant_baseline == "central":
            baseline_offset = state.font_size * 0.35
        elif state.dominant_baseline == "hanging":
            baseline_offset = -state.font_size * 0.8
        elif state.dominant_baseline == "middle":
            baseline_offset = state.font_size * 0.25
        else:  # auto, alphabetic, etc.
            baseline_offset = 0

        # Render each character
        cursor_x = 0.0

        for char in text:
            if char == " ":
                # Space - advance cursor without drawing
                try:
                    glyph = cache.get_glyph(state.font_path, "n", font=font)
                    cursor_x += glyph.advance_width * scale
                except ValueError:
                    cursor_x += state.font_size * 0.3
                continue

            try:
                glyph = cache.get_glyph(state.font_path, char, font=font)
            except ValueError:
                # Character not in font - skip
                continue

            if glyph.path:
                path_kwargs = {
                    "d": glyph.path,
                    "fill_rule": "evenodd",
                }
                self._set_fill_and_stroke_kwargs(state, path_kwargs, drawing)
                path = dw.Path(**path_kwargs)

                # Apply transform: scale and position
                # Cache stores paths at scale=1, flip_y=True, origin at baseline
                tx = cursor_x + anchor_offset
                ty = baseline_offset
                transform = f"translate({tx:.3f},{ty:.3f}) scale({scale:.6f})"
                _set_elem_attr(path, "transform", transform)

                group.append(path)

            # Advance cursor
            cursor_x += glyph.advance_width * scale

        return group

    def _calculate_text_width(
        self, font_path: str, text: str, scale: float, cache
    ) -> float:
        """Calculate total text width for alignment."""
        width = 0.0
        for char in text:
            if char == " ":
                try:
                    glyph = cache.get_glyph(font_path, "n")
                    width += glyph.advance_width * scale
                except ValueError:
                    width += scale * 500  # Fallback
            else:
                try:
                    glyph = cache.get_glyph(font_path, char)
                    width += glyph.advance_width * scale
                except ValueError:
                    pass
        return width
