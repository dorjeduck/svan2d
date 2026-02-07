"""Rectangle renderer implementation using new architecture"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import drawsvg as dw

from .base import Renderer

if TYPE_CHECKING:
    from ..state.rectangle import RectangleState




class RectangleRenderer(Renderer):
    """Renderer class for rendering rectangle elements"""

    def _render_core(
        self, state: "RectangleState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Rectangle:
        """Render the rectangle renderer (geometry only, no transforms)

        Args:
            state (RectangleState): The state of the rectangle

        Returns:
            dw.Rectangle: The drawsvg rectangle object
        """
        # Create rectangle centered at origin with scaled dimensions
        rect_kwargs = {
            "x": -(state.width) / 2,  # Center the rectangle
            "y": -(state.height) / 2,
            "width": state.width,
            "height": state.height,
        }

        if state.corner_radius > 0:
            # Clamp to max valid radius
            max_radius = min(state.width, state.height) / 2
            r = min(state.corner_radius, max_radius)
            rect_kwargs["rx"] = r
            rect_kwargs["ry"] = r

        self._set_fill_and_stroke_kwargs(state, rect_kwargs, drawing)

        return dw.Rectangle(**rect_kwargs)
