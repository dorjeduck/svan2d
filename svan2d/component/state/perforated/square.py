"""Perforated Square state - Square with  holes"""

from __future__ import annotations
from dataclasses import dataclass

from svan2d.core.point2d import Point2D

from .base import PerforatedVertexState
from svan2d.component.state.base import State
from svan2d.component.vertex import VertexSquare, VertexLoop
from svan2d.transition import easing


@dataclass(frozen=True)
class PerforatedSquareState(PerforatedVertexState):
    """Square with  holes

    A square outer shape with zero or more vertex loops of arbitrary shapes.

    Args:
        size: Square size
         holes : List of Shape objects specifying hole geometry and positions

    Example:
        PerforatedSquareState(
            width=200,
            height=150,
             holes =[
                Circle(radius=20, x=-50, y=0),
                Circle(radius=20, x=50, y=0),
            ],
            fill_color=Color("#E74C3C"),
        )
    """

    size: float = 160

    DEFAULT_EASING = {
        **PerforatedVertexState.DEFAULT_EASING,
        "size": easing.in_out,
    }

    def _generate_outer_contour(self) -> VertexLoop:
        """Generate rectangular outer contour"""
        return VertexSquare(
            center=Point2D(), size=self.size, num_vertices=self._num_vertices
        )
