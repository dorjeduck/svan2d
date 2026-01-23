from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from svan2d.component.registry import renderer
from svan2d.component.renderer.wave import WaveRenderer
from svan2d.component.state.base_vertex import VertexState
from svan2d.component.state.line import line_endpoints_to_center_rotation_length
from svan2d.component.vertex import VertexContours
from svan2d.core.point2d import Point2D


@renderer(WaveRenderer)
@dataclass(frozen=True)
class WaveState(VertexState):
    """Sine wave - OPEN shape"""

    length: float = 100
    amplitude: float = 20
    frequency: float = 2  # Number of complete waves
    closed: bool = False

    @staticmethod
    def from_endpoints(
        x1:float,y1:float,x2:float,y2:float,
        amplitude:float,
        frequency:float,
        scale:Optional[float]=None,
        opacity:Optional[float]=None,
    )-> WaveState:
        cx, cy, calc_rotation, length =  line_endpoints_to_center_rotation_length(x1,y1,x2,y2)
        return WaveState(
            x=cx,
            y=cy,
            rotation=calc_rotation,
            length=length,
            amplitude=amplitude,
            frequency=frequency,
            scale=scale,
            opacity=opacity,
        )

    def _generate_contours(self) -> VertexContours:
        """Generate wave vertices"""
        vertices = []
        half_length = self.length / 2
        assert self._num_vertices is not None

        for i in range(self._num_vertices):
            t = i / (self._num_vertices - 1) if self._num_vertices > 1 else 0
            x = -half_length + t * self.length
            y = self.amplitude * math.sin(t * self.frequency * 2 * math.pi)
            vertices.append(Point2D(x, y))

        return VertexContours.from_single_loop(vertices, closed=self.closed)
