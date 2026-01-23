"""Ring state implementation using VertexContours"""

from __future__ import annotations

from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.ring import RingRenderer
from svan2d.component.vertex import VertexCircle, VertexContours
from svan2d.core.point2d import Point2D

from .base_vertex import VertexState


@renderer(RingRenderer)
@dataclass(frozen=True)
class RingState(VertexState):
    """State class for ring elements (circle with circular hole)"""

    inner_radius: float = 50
    outer_radius: float = 70

    def _generate_contours(self) -> VertexContours:
        """Generate ring contours with outer and inner circles

        Returns VertexContours with:
        - Outer: larger circle (counter-clockwise)
        - Hole: smaller circle (clockwise, creates the hole)
        """
        assert self._num_vertices is not None
        # Generate outer circle (counter-clockwise winding)
        outer_circle = VertexCircle(
            center=Point2D(),
            radius=self.outer_radius,
            num_vertices=self._num_vertices,
            start_angle=0.0,
        )

        # Generate inner circle as a hole (clockwise winding)
        # We achieve clockwise by reversing the vertices
        inner_circle = VertexCircle(
            center=Point2D(),
            radius=self.inner_radius,
            num_vertices=self._num_vertices,
            start_angle=0.0,
        )
        inner_circle_reversed = inner_circle.reverse()

        return VertexContours(outer=outer_circle, holes=[inner_circle_reversed])
