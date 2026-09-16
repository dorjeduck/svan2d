"""Arc renderer implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import drawsvg as dw

from .base import Renderer

if TYPE_CHECKING:
    from svan2d.primitive.state.arc import ArcState


class ArcRenderer(Renderer):

    def _render_core(
        self, state: ArcState, drawing: dw.Drawing | None = None
    ) -> dw.Path:
        """Render arc using SVG path primitive"""
        import math

        start_rad = math.radians(state.start_angle)
        end_rad = math.radians(state.end_angle)

        # Calculate start and end points: 0° = East, CCW positive (negate y for SVG Y-down)
        start_x = state.radius * math.cos(start_rad)
        start_y = -state.radius * math.sin(start_rad)
        end_x = state.radius * math.cos(end_rad)
        end_y = -state.radius * math.sin(end_rad)

        # Determine if we need the large arc flag
        angle_diff = end_rad - start_rad
        large_arc = 1 if abs(angle_diff) > math.pi else 0
        # Y is negated, so a positive angle sweeps CCW on screen: sweep flag 0.
        sweep = 0 if angle_diff > 0 else 1

        path_kwargs = {}
        self._set_fill_and_stroke_kwargs(state, path_kwargs, drawing)
        path = dw.Path(**path_kwargs)

        path.M(start_x, start_y)
        if abs(angle_diff) >= 2 * math.pi:
            # Coincident endpoints make a single arc degenerate: draw two half arcs.
            mid_rad = start_rad + (math.pi if angle_diff > 0 else -math.pi)
            mid_x = state.radius * math.cos(mid_rad)
            mid_y = -state.radius * math.sin(mid_rad)
            path.A(state.radius, state.radius, 0, 0, sweep, mid_x, mid_y)
            path.A(state.radius, state.radius, 0, 0, sweep, start_x, start_y)
        else:
            path.A(state.radius, state.radius, 0, large_arc, sweep, end_x, end_y)

        return path
