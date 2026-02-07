"""Square state implementation using VertexRectangle"""

from __future__ import annotations

from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.square import SquareRenderer
from svan2d.component.vertex import VertexContours, VertexRectangle
from svan2d.core.point2d import Point2D

from .base_vertex import VertexState


@renderer(SquareRenderer)
@dataclass(frozen=True)
class SquareState(VertexState):
    """State class for square elements"""

    size: float = 100
    corner_radius: float = 0

    def _generate_contours(self) -> VertexContours:
        """Generate square contours using VertexRectangle"""
        assert self._num_vertices is not None
        square = VertexRectangle(
            center=Point2D(),
            width=self.size,
            height=self.size,
            num_vertices=self._num_vertices,
            corner_radius=self.corner_radius,
        )
        return VertexContours(outer=square, holes=None)
