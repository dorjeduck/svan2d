"""Perforated rectangle state - rectangle with  holes"""

from __future__ import annotations

from dataclasses import dataclass

from svan2d.component.vertex import VertexLoop, VertexRectangle
from svan2d.core.point2d import Point2D

from .base import PerforatedVertexState


@dataclass(frozen=True)
class PerforatedRectangleState(PerforatedVertexState):
    """Rectangle with  holes

    A rectangular outer shape with zero or more vertex loops of arbitrary shapes.

    Args:
        width: Rectangle width
        height: Rectangle height
         holes : List of Shape objects specifying hole geometry and positions

    Example:
        PerforatedRectangleState(
            width=200,
            height=150,
             holes =[
                Circle(radius=20, x=-50, y=0),
                Circle(radius=20, x=50, y=0),
            ],
            fill_color=Color("#E74C3C"),
        )
    """

    width: float = 160
    height: float = 100

    def _generate_outer_contour(self) -> VertexLoop:
        """Generate rectangular outer contour"""
        assert self._num_vertices is not None
        return VertexRectangle(
            center=Point2D(),
            width=self.width,
            height=self.height,
            num_vertices=self._num_vertices,
        )
