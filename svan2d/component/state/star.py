"""Star renderer implementation using new architecture"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple

from svan2d.component.state.base_vertex import VertexState
from svan2d.component.vertex import VertexContours, VertexStar
from svan2d.component.registry import renderer
from svan2d.component.renderer.star import StarRenderer
from svan2d.core.point2d import Point2D

from .base import State
from svan2d.transition import easing
from svan2d.core.color import Color


@renderer(StarRenderer)
@dataclass(frozen=True)
class StarState(VertexState):
    """State class for star elements"""

    outer_radius: float = 50  # Radius to outer points
    inner_radius: float = 20  # Radius to inner points
    num_points_star: int = 5  # Number of points (minimum 3)

    DEFAULT_EASING = {
        **State.DEFAULT_EASING,
        "outer_radius": easing.in_out,
        "inner_radius": easing.in_out,
        "num_points_star": easing.linear,  # Stepped animation for integers
    }

    def __post_init__(self):
        super().__post_init__()
        self._none_color("fill_color")
        self._none_color("stroke_color")

    def _generate_contours(self) -> VertexContours:
        """Generate star vertices"""
        star = VertexStar(
            center=Point2D(),
            outer_radius=self.outer_radius,
            inner_radius=self.inner_radius,
            num_points=self.num_points_star,
            num_vertices=self._num_vertices,
        )
        return VertexContours(outer=star, holes=None)
