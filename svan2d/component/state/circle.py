from __future__ import annotations

from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.circle import CircleRenderer
from svan2d.component.vertex import VertexCircle, VertexContours
from svan2d.core.point2d import Point2D

from .base import State
from .base_vertex import VertexState


@renderer(CircleRenderer)
@dataclass(frozen=True)
class CircleState(VertexState):
    """State class for circle elements"""

    radius: float = 50

    def _generate_contours(self) -> VertexContours:
        """Generate circle contours

        Returns VertexContours with a single circular outer contour, no  vertex_loops .
        """
        assert self._num_vertices is not None
        circle = VertexCircle(
            Point2D(0, 0),
            radius=self.radius,
            num_vertices=self._num_vertices,
            start_angle=0.0,
        )

        return VertexContours(outer=circle, holes=None)
