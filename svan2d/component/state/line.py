"""Line state implementation using VertexContours"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from svan2d.component.registry import renderer
from svan2d.component.renderer.line import LineRenderer
from svan2d.component.state.base_vertex import VertexState
from svan2d.component.vertex import VertexContours
from svan2d.core.point2d import Point2D


@renderer(LineRenderer)
@dataclass(frozen=True)
class LineState(VertexState):
    """State class for line elements"""

    length: float = 100  # Length of the line
    stroke_dasharray: str | None = None  # For dashed lines, e.g., "5,5"
    stroke_linecap: str = "round"  # "butt", "round", "square"
    draw_progress: float = 1.0  # Fraction of polyline to draw (0.0–1.0)
    closed: bool = False

    def __post_init__(self):
        super().__post_init__()
        self._none_color("stroke_color")

    @staticmethod
    def from_endpoints(
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke_color: str | None = None,
        stroke_width: float | None = None,
        stroke_dasharray: str | None = None,
        stroke_linecap: str | None = None,
        scale: float | None = None,
        rotation: float | None = None,
        opacity: float | None = None,
    ) -> LineState:

        cx, cy, add_rotation, length = line_endpoints_to_center_rotation_length(
            x1, y1, x2, y2
        )
        return LineState(
            pos=Point2D(cx, cy),
            rotation=(rotation or 0) + add_rotation,
            length=length,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            stroke_dasharray=stroke_dasharray,
            stroke_linecap=stroke_linecap,
            scale=scale,
            opacity=opacity,
        )

    def _generate_contours(self) -> VertexContours:
        """Generate line contours from -length/2 to +length/2 along x-axis"""
        half_length = self.length / 2

        assert self._num_vertices is not None
        vertices = [
            Point2D(-half_length + (i / (self._num_vertices - 1)) * self.length, 0)
            for i in range(self._num_vertices)
        ]

        return VertexContours.from_single_loop(vertices, closed=self.closed)


def line_endpoints_to_center_rotation_length(
    x1: float, y1: float, x2: float, y2: float
) -> Tuple[float, float, float, float]:
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    rotation = math.atan2(y2 - y1, x2 - x1)
    length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return center_x, center_y, rotation, length


def line_center_rotation_length_to_endpoints(
    center: Point2D, rotation: float, length: float
) -> Tuple[float, float, float, float]:
    # Calculate the endpoints based on the center, rotation, and length
    # take rotation into account

    theta = math.radians(90 - rotation)
    h = length / 2
    dx = math.cos(theta)
    dy = math.sin(theta)

    x1 = center.x - h * dx
    y1 = center.y - h * dy
    x2 = center.x + h * dx
    y2 = center.y + h * dy

    return x1, y1, x2, y2
