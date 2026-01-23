"""Rectangle renderer implementation using new architecture"""

from __future__ import annotations

from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.square import SquareRenderer
from svan2d.component.vertex import VertexContours
from svan2d.core.point2d import Point2D

from .base_vertex import VertexState


@renderer(SquareRenderer)
@dataclass(frozen=True)
class SquareState(VertexState):
    """State class for rectangle elements"""

    size: float = 100

    def _generate_contours(self) -> VertexContours:
        """Generate square vertices, starting at top-left, going clockwise"""
        half = self.size / 2
        perimeter = 4 * self.size

        assert self._num_vertices is not None
        vertices = []
        for i in range(self._num_vertices - 1):
            distance = (i / (self._num_vertices - 1)) * perimeter

            if distance < self.size:  # Top edge
                x = -half + distance
                y = -half
            elif distance < 2 * self.size:  # Right edge
                x = half
                y = -half + (distance - self.size)
            elif distance < 3 * self.size:  # Bottom edge
                x = half - (distance - 2 * self.size)
                y = half
            else:  # Left edge
                x = -half
                y = half - (distance - 3 * self.size)

            vertices.append(Point2D(x, y))

        vertices.append(vertices[0])
        return VertexContours.from_single_loop(vertices, closed=True)
