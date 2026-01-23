"""Perforated Square state - Square with  holes"""

from __future__ import annotations

from dataclasses import dataclass

from svan2d.component.vertex import VertexLoop, VertexSquare
from svan2d.core.point2d import Point2D

from .base import PerforatedVertexState


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

    def _generate_outer_contour(self) -> VertexLoop:
        """Generate rectangular outer contour"""
        assert self._num_vertices is not None
        return VertexSquare(
            center=Point2D(), size=self.size, num_vertices=self._num_vertices
        )
