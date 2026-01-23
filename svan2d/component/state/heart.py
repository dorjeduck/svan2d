from __future__ import annotations

import math
from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.heart import HeartRenderer
from svan2d.component.state.base_vertex import VertexState
from svan2d.component.vertex import VertexContours
from svan2d.core.point2d import Point2D


@renderer(HeartRenderer)
@dataclass(frozen=True)
class HeartState(VertexState):
    """Heart shape using parametric equations"""

    size: float = 50

    def _generate_contours(self) -> VertexContours:
        """Generate heart vertices using parametric equations"""
        vertices = []

        assert self._num_vertices is not None
        for i in range(self._num_vertices - 1):
            # Parameter t goes from 0 to 2π
            t = (i / (self._num_vertices - 1)) * 2 * math.pi

            # Heart curve parametric equations
            x = 16 * math.sin(t) ** 3
            y = -(
                13 * math.cos(t)
                - 5 * math.cos(2 * t)
                - 2 * math.cos(3 * t)
                - math.cos(4 * t)
            )

            # Scale to desired size
            scale = self.size / 20
            vertices.append(Point2D(x * scale, y * scale))

        vertices.append(vertices[0])
        return VertexContours.from_single_loop(vertices, closed=True)
