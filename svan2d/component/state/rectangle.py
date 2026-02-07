"""Rectangle state implementation using VertexContours"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from svan2d.component.registry import renderer
from svan2d.component.renderer.rectangle import RectangleRenderer
from svan2d.component.vertex import VertexContours, VertexRectangle
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D

from .base_vertex import VertexState


@renderer(RectangleRenderer)
@dataclass(frozen=True)
class RectangleState(VertexState):
    """State class for rectangle elements"""

    width: float = 100
    height: float = 60
    fill_color: Optional[Color] = Color(0, 0, 255)
    fill_opacity: float = 1
    stroke_color: Optional[Color] = Color.NONE
    stroke_opacity: float = 1
    corner_radius: float = 0

    def __post_init__(self):
        super().__post_init__()
        self._none_color("fill_color")
        self._none_color("stroke_color")

    def _generate_contours(self) -> VertexContours:
        """Generate rectangle contours

        Returns VertexContours with a single rectangular outer contour, no vertex_loops.
        """
        assert self._num_vertices is not None
        rectangle = VertexRectangle(
            center=Point2D(),
            width=self.width,
            height=self.height,
            num_vertices=self._num_vertices,
            corner_radius=self.corner_radius,
        )

        return VertexContours(outer=rectangle, holes=None)
