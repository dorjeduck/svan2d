from __future__ import annotations
from dataclasses import dataclass

from svan2d.core.point2d import Point2D

from .base import State
from .base_vertex import VertexState
from svan2d.component.vertex import VertexContours, VertexCircle
from svan2d.component.registry import renderer
from svan2d.component.renderer.circle import CircleRenderer
from svan2d.transition import easing


@renderer(CircleRenderer)
@dataclass(frozen=True)
class CircleState(VertexState):
    """State class for circle elements"""

    radius: float = 50

    # Default easing functions for each field
    DEFAULT_EASING = {
        **State.DEFAULT_EASING,
        "radius": easing.in_out,
    }

    def _generate_contours(self) -> VertexContours:
        """Generate circle contours

        Returns VertexContours with a single circular outer contour, no  vertex_loops .
        """
        circle = VertexCircle(
            Point2D(0, 0),
            radius=self.radius,
            num_vertices=self._num_vertices,
            start_angle=0.0,
        )

        return VertexContours(outer=circle, holes=None)
