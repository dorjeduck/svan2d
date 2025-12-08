"""Line renderer implementation using new architecture"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional


import math
import drawsvg as dw

from svan2d.core.point2d import Point2D

from .base import Renderer

if TYPE_CHECKING:
    from ..state.line import LineState


class LineRenderer(Renderer):
    @staticmethod
    def from_endpoints(start: Point2D, end: Point2D):
        """
        Given two endpoints, return center (x, y), length, and rotation (degrees).
        Returns:
            (cx, cy, length, rotation)
        """
        center = start.center_to(end)
        length = start.distance_to(end)
        rotation = start.rotation_to(end)
        return center, length, rotation

    """Renderer class for rendering line elements"""

    def _render_core(
        self, state: "LineState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Line:
        """Render the line renderer (geometry only, no transforms)

        Args:
            state: The state object containing attributes for rendering

        Returns:
            drawsvg Line object representing the line renderer
        """

        # Create line with basic attributes
        line_kwargs = {
            "stroke_linecap": state.stroke_linecap,
        }
        self._set_fill_and_stroke_kwargs(state, line_kwargs, drawing)
        # Add stroke dash array if specified
        if state.stroke_dasharray:
            line_kwargs["stroke_dasharray"] = state.stroke_dasharray

        # Remove manual opacity and rotation
        half_length = state.length / 2

        # Center at origin, let base handle translation and rotation
        start_x = -half_length
        start_y = 0

        end_x = half_length
        end_y = 0

        # Line constructor takes (sx, sy, ex, ey, **kwargs)
        return dw.Line(start_x, start_y, end_x, end_y, **line_kwargs)
