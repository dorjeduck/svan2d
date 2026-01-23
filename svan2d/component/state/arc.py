from __future__ import annotations

import math
from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.arc import ArcRenderer
from svan2d.component.state.base_vertex import VertexState
from svan2d.component.vertex import VertexContours
from svan2d.core.point2d import Point2D


@renderer(ArcRenderer)
@dataclass(frozen=True)
class ArcState(VertexState):
    """Circular arc - OPEN shape"""

    radius: float = 50
    start_angle: float = 0  # Degrees
    end_angle: float = 180  # Degrees
    closed: bool = False  # Arcs are open by default

    def _generate_contours(self) -> VertexContours:
        """Generate arc vertices"""
        vertices = []

        start_rad = math.radians(self.start_angle)
        end_rad = math.radians(self.end_angle)
        angle_range = end_rad - start_rad

        assert self._num_vertices is not None
        for i in range(self._num_vertices):
            t = i / (self._num_vertices - 1) if self._num_vertices > 1 else 0
            angle = start_rad + t * angle_range

            vertices.append(
                Point2D(self.radius * math.sin(angle), -self.radius * math.cos(angle))
            )

        return VertexContours.from_single_loop(vertices, closed=self.closed)
