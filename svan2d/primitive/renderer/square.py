"""Square renderer implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import drawsvg as dw

from .base import Renderer

if TYPE_CHECKING:
    from ..state.square import SquareState




class SquareRenderer(Renderer):
    """Renderer for square elements."""

    def _render_core(
        self, state: "SquareState", drawing: dw.Drawing | None = None
    ) -> dw.Rectangle:
        """Render the square geometry centered at origin (no transforms).

        Args:
            state: The SquareState to render.

        Returns:
            dw.Rectangle: The drawsvg rectangle object.
        """


        # Create rectangle centered at origin with scaled dimensions
        rect_kwargs = {
            "x": -(state.size) / 2,  # Center the rectangle
            "y": -(state.size) / 2,
            "width": state.size,
            "height": state.size,
        }

        if state.corner_radius > 0:
            # Clamp to max valid radius
            max_radius = state.size / 2
            r = min(state.corner_radius, max_radius)
            rect_kwargs["rx"] = r
            rect_kwargs["ry"] = r

        self._set_fill_and_stroke_kwargs(state, rect_kwargs, drawing)

        return dw.Rectangle(**rect_kwargs)
