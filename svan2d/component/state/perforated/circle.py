"""Perforated circle state - circle with  holes"""

from __future__ import annotations
from dataclasses import dataclass

from svan2d.core.point2d import Point2D

from .base import PerforatedVertexState
from svan2d.component.state.base import State
from svan2d.component.vertex import VertexCircle, VertexLoop
from svan2d.transition import easing


@dataclass(frozen=True)
class PerforatedCircleState(PerforatedVertexState):
    """Circle with  holes

    A circular outer shape with zero or more vertex loops of arbitrary shapes.

    Args:
        radius: Circle radius
         holes : List of Shape objects specifying hole geometry and positions

    Example:
        PerforatedCircleState(
            radius=100,
             holes =[
                Circle(radius=20, x=-30, y=0),
                Star(outer_radius=15, inner_radius=7, num_points=5, x=30, y=0),
            ],
            fill_color=Color("#4ECDC4"),
        )
    """

    radius: float = 100

    DEFAULT_EASING = {
        **PerforatedVertexState.DEFAULT_EASING,
        "radius": easing.in_out,
    }

    def _generate_outer_contour(self) -> VertexLoop:
        """Generate circular outer contour"""
        return VertexCircle(
            Point2D(0, 0), radius=self.radius, num_vertices=self._num_vertices
        )
