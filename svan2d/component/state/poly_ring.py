"""Polygon ring state implementation using VertexContours"""

from __future__ import annotations

from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.poly_ring import PolyRingRenderer
from svan2d.component.vertex import VertexContours, VertexRegularPolygon
from svan2d.core.point2d import Point2D

from .base_vertex import VertexState


@renderer(PolyRingRenderer)
@dataclass(frozen=True)
class PolyRingState(VertexState):
    """State class for polygon ring elements (polygon with polygon hole)

    A generic ring shape with customizable number of edges for both
    the outer and inner polygons. The inner polygon can be rotated
    independently using inner_rotation. Use the base rotation parameter
    to rotate the entire shape.

    Rotation follows svan2d convention: 0° = North (up), 90° = East (right)
    """

    inner_size: float = 50
    outer_size: float = 70
    num_edges: int = 6  # Number of edges (3=triangle, 4=square, 5=pentagon, etc.)
    inner_rotation: float = 0  # Rotation of inner polygon in degrees

    def _generate_contours(self) -> VertexContours:
        """Generate polygon ring contours with outer and inner polygons

        Returns VertexContours with:
        - Outer: larger polygon (counter-clockwise)
        - Hole: smaller polygon (clockwise, creates the hole)

        The inner polygon can be rotated independently using inner_rotation.
        """
        assert self._num_vertices is not None
        # Generate outer polygon (counter-clockwise winding)
        outer_polygon = VertexRegularPolygon(
            center=Point2D(),
            size=self.outer_size,
            num_sides=self.num_edges,
            num_vertices=self._num_vertices,
            rotation=0,
        )

        # Generate inner polygon as a hole (clockwise winding)
        # We achieve clockwise by reversing the vertices
        inner_polygon = VertexRegularPolygon(
            center=Point2D(),
            size=self.inner_size,
            num_sides=self.num_edges,
            num_vertices=self._num_vertices,
            rotation=self.inner_rotation,
        )

        inner_polygon_reversed = inner_polygon.reverse()

        return VertexContours(outer=outer_polygon, holes=[inner_polygon_reversed])
