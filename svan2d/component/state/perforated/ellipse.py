"""Perforated ellipse state - ellipse with  holes"""

from __future__ import annotations
from dataclasses import dataclass

from svan2d.core.point2d import Point2D

from .base import PerforatedVertexState
from svan2d.component.vertex import VertexEllipse, VertexLoop
from svan2d.transition import easing


@dataclass(frozen=True)
class PerforatedEllipseState(PerforatedVertexState):
    """Ellipse with  holes

    An elliptical outer shape with zero or more vertex loops of arbitrary shapes.

    Args:
        rx: Horizontal radius (semi-major axis)
        ry: Vertical radius (semi-minor axis)
         holes : List of Shape objects specifying hole geometry and positions

    Example:
        PerforatedEllipseState(
            rx=120,
            ry=80,
            holes=[Circle(radius=20, x=-40, y=0), Circle(radius=20, x=40, y=0)],
            fill_color=Color("#9B59B6"),
        )
    """

    rx: float = 100
    ry: float = 60

    DEFAULT_EASING = {
        **PerforatedVertexState.DEFAULT_EASING,
        "rx": easing.in_out,
        "ry": easing.in_out,
    }

    def _generate_outer_contour(self) -> VertexLoop:
        """Generate elliptical outer contour"""
        return VertexEllipse(
            center=Point2D(), rx=self.rx, ry=self.ry, num_vertices=self._num_vertices
        )
