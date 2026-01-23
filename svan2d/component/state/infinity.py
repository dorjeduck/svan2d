from __future__ import annotations

import math
from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.infinity import InfinityRenderer
from svan2d.component.state.base_vertex import VertexState
from svan2d.component.vertex import VertexContours
from svan2d.core.point2d import Point2D


@renderer(InfinityRenderer)
@dataclass(frozen=True)
class InfinityState(VertexState):
    """Infinity symbol (lemniscate)"""

    size: float = 50

    def _generate_contours(self) -> VertexContours:
        """Generate infinity symbol using lemniscate parametric equations"""
        vertices = []

        assert self._num_vertices is not None
        for i in range(self._num_vertices - 1):
            t = (i / (self._num_vertices - 1)) * 2 * math.pi

            # Lemniscate of Bernoulli
            # x = a * cos(t) / (1 + sin²(t))
            # y = a * sin(t) * cos(t) / (1 + sin²(t))
            denominator = 1 + math.sin(t) ** 2
            x = self.size * math.cos(t) / denominator
            y = self.size * math.sin(t) * math.cos(t) / denominator

            vertices.append(Point2D(x, y))

        vertices.append(vertices[0])
        return VertexContours.from_single_loop(vertices, closed=True)
