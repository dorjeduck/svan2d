"""Number renderer implementation - handles aligned decimal point rendering"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

import drawsvg as dw

from .base import Renderer

if TYPE_CHECKING:
    from ..state.number import NumberState


class NumberRenderer(Renderer):
    """Renderer for number elements

    Supports two rendering modes:
    1. Standard: Single text element (INTEGER, AUTO, FIXED formats)
    2. Aligned: Two text elements for decimal point alignment (AUTO_ALIGNED, FIXED_ALIGNED formats)

    For AUTO_ALIGNED and FIXED_ALIGNED formats, renders the integer and decimal
    parts separately to keep the decimal point at the same x-position:
    - Integer part: text-anchor="end" (right-aligned at x=0)
    - Decimal part: text-anchor="start" (left-aligned at x=0)
    Both positioned at x=0, creating a fixed decimal point position.

    The actual number interpolation happens at the state level:
    - value field interpolates smoothly (0.0 → 100.0)
    - text field is regenerated at each interpolation step
    - format/decimals/prefix/suffix use step interpolation
    """

    def _render_core(
        self, state: "NumberState", drawing: Optional[dw.Drawing] = None
    ) -> Union[dw.Text, dw.Group]:
        """Render the formatted number as text

        Args:
            state: NumberState containing formatted text
            drawing: Optional drawing context

        Returns:
            drawsvg Text element or Group (for aligned rendering)
        """
        # Check if we need aligned decimal point rendering
        # Compare against the string value of the enum
        if str(state.format) in ("auto_aligned", "fixed_aligned"):
            return self._render_aligned(state, drawing)
        else:
            return self._render_standard(state, drawing)

    def _render_standard(
        self, state: "NumberState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Text:
        """Render as single text element (standard mode)"""
        text_kwargs = {
            "text": state.text,
            "x": 0,
            "y": 0,
            "font_family": state.font_family,
            "font_size": state.font_size,
            "font_weight": state.font_weight,
            "text_anchor": state.text_anchor,
            "letter_spacing": state.letter_spacing,
            "dominant_baseline": state.dominant_baseline,
        }
        self._set_fill_and_stroke_kwargs(state, text_kwargs, drawing)

        return dw.Text(**text_kwargs)  # type: ignore[return-value]

    def _render_aligned(
        self, state: "NumberState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Group:
        """Render with aligned decimal point (two text elements)

        Creates two text elements:
        1. Integer part + prefix: text-anchor="end" (right-aligned at x=0)
        2. Decimal part + suffix: text-anchor="start" (left-aligned at x=0)

        This keeps the decimal point at x=0 regardless of the number of digits.
        The decimal point is literally at the element's x=0 position (center).

        Example layout at x=0:
            "12" (end) | ".34" (start)
                     ^ decimal point at x=0
        """
        group = dw.Group()

        # Base text styling (override text_anchor for alignment)
        base_kwargs = {
            "y": 0,
            "font_family": state.font_family,
            "font_size": state.font_size,
            "font_weight": state.font_weight,
            "letter_spacing": state.letter_spacing,
            "dominant_baseline": state.dominant_baseline,
        }

        # Integer part (right-aligned at x=0)
        # This makes the RIGHT EDGE of the text at x=0
        int_kwargs = {
            **base_kwargs,
            "text": state.prefix + state._integer_part,
            "x": 0,
            "text_anchor": "end",  # Right edge at x=0
        }
        self._set_fill_and_stroke_kwargs(state, int_kwargs, drawing)
        group.append(dw.Text(**int_kwargs))

        # Decimal part (left-aligned at x=0)
        # This makes the LEFT EDGE of the text at x=0
        if state._has_decimals:
            dec_text = state._decimal_part + state.suffix
        else:
            # No decimals, but we might have a suffix
            dec_text = state.suffix

        if dec_text:  # Only render if there's something to show
            dec_kwargs = {
                **base_kwargs,
                "text": dec_text,
                "x": 0,
                "text_anchor": "start",  # Left edge at x=0
            }
            self._set_fill_and_stroke_kwargs(state, dec_kwargs, drawing)
            group.append(dw.Text(**dec_kwargs))

        return group
