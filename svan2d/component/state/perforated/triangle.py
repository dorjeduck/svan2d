"""Perforated triangle state - triangle with  holes"""

from __future__ import annotations
from dataclasses import dataclass

from svan2d.core.point2d import Point2D

from .base import PerforatedVertexState
from svan2d.component.state.base import State
from svan2d.component.vertex import VertexTriangle, VertexLoop
from svan2d.transition import easing


@dataclass(frozen=True)
class PerforatedTriangleState(PerforatedVertexState):
    """Triangle with  holes

    A triangular outer shape with zero or more vertex loops of arbitrary shapes.

    Args:
        size: Size of the triangle (distance from center to vertices)
         holes : List of Shape objects specifying hole geometry and positions

    Example:
        PerforatedTriangleState(
            size=100,
             holes =[Circle(radius=20, x=0, y=10)],
            fill_color=Color("#2ECC71"),
        )
    """

    size: float = 100

    DEFAULT_EASING = {
        **PerforatedVertexState.DEFAULT_EASING,
        "size": easing.in_out,
    }

    def _generate_outer_contour(self) -> VertexLoop:
        """Generate triangular outer contour"""
        return VertexTriangle(
            center=Point2D(), size=self.size, num_vertices=self._num_vertices
        )
