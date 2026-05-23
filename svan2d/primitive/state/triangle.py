"""Triangle renderer implementation using new architecture"""

from __future__ import annotations

import math
from dataclasses import dataclass
from svan2d.primitive.registry import renderer, skia_renderer
from svan2d.primitive.renderer.triangle import TriangleRenderer
from svan2d.primitive.vertex import VertexContours
from svan2d.core.point2d import Point2D

from .base_vertex import VertexState


@skia_renderer("svan2d.primitive.renderer.skia.triangle:TriangleSkiaRenderer")
@renderer(TriangleRenderer)
@dataclass(frozen=True)
class TriangleState(VertexState):
    """State class for triangle elements"""

    size: float = 50  # Size of the triangle (distance from center to vertex)

    def __post_init__(self):
        super().__post_init__()
        self._none_color("fill_color")
        self._none_color("stroke_color")

    def _generate_contours(self) -> VertexContours:
        """Generate triangle vertices distributed along perimeter

        Apex points up, matching TriangleRenderer. The three corners are:
        - Apex (top):    90°
        - Lower-left:   210°
        - Lower-right:  330°

        The last vertex equals the first to close the loop.
        """
        # Corners apex-up so contours match what TriangleRenderer draws.
        triangle_verts = []
        for i in range(3):
            angle = math.radians(90 + i * 120)
            triangle_verts.append(
                Point2D(self.size * math.cos(angle), -self.size * math.sin(angle))
            )

        # Calculate perimeter lengths between vertices

        edge_lengths = [
            triangle_verts[i].distance_to(triangle_verts[(i + 1) % 3]) for i in range(3)
        ]
        total_perimeter = sum(edge_lengths)

        # Distribute num_points - 1 vertices along the perimeter
        vertices = []
        assert self._num_vertices is not None

        for i in range(self._num_vertices - 1):
            target_distance = (i / (self._num_vertices - 1)) * total_perimeter

            # Find which edge we're on
            cumulative = 0
            current_edge = 0
            distance_along_edge = 0.0
            for edge_idx in range(3):
                if cumulative + edge_lengths[edge_idx] >= target_distance:
                    current_edge = edge_idx
                    distance_along_edge = target_distance - cumulative
                    break
                cumulative += edge_lengths[edge_idx]

            # Interpolate along current edge
            v1 = triangle_verts[current_edge]
            v2 = triangle_verts[(current_edge + 1) % 3]
            t = distance_along_edge / edge_lengths[current_edge]

            x = v1.x + t * (v2.x - v1.x)
            y = v1.y + t * (v2.y - v1.y)
            vertices.append(Point2D(x, y))

        # Last vertex equals first vertex (complete the loop)
        vertices.append(vertices[0])

        return VertexContours.from_single_loop(vertices, closed=True)
