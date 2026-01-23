"""Perforated polygon state - regular polygon with  holes"""

from __future__ import annotations

from dataclasses import dataclass

from svan2d.component.vertex import VertexLoop, VertexRegularPolygon
from svan2d.core.point2d import Point2D

from .base import PerforatedVertexState


@dataclass(frozen=True)
class PerforatedPolygonState(PerforatedVertexState):
    """Regular polygon with  holes

    A regular polygon outer shape with zero or more vertex loops of arbitrary shapes.

    Args:
        num_sides: Number of sides (3 = triangle, 5 = pentagon, 6 = hexagon, etc.)
        size: Radius of circumscribed circle
         holes : List of Shape objects specifying hole geometry and positions

    Example:
        PerforatedPolygonState(
            num_sides=6,
            size=100,
             holes =[Circle(radius=30, x=0, y=0)],
            fill_color=Color("#3498DB"),
        )
    """

    num_sides: int = 6
    size: float = 100

    def _generate_outer_contour(self) -> VertexLoop:
        """Generate regular polygon outer contour"""
        assert self._num_vertices is not None
        return VertexRegularPolygon(
            center=Point2D(),
            size=self.size,
            num_sides=self.num_sides,
            num_vertices=self._num_vertices,
            rotation=0,
        )
