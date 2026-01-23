"""Ellipse state implementation using VertexContours"""

from __future__ import annotations

from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.ellipse import EllipseRenderer
from svan2d.component.state.base_vertex import VertexState
from svan2d.component.vertex import VertexContours, VertexEllipse
from svan2d.core.point2d import Point2D


@renderer(EllipseRenderer)
@dataclass(frozen=True)
class EllipseState(VertexState):
    """State class for ellipse elements"""

    rx: float = 60  # Horizontal radius
    ry: float = 40  # Vertical radius

    def __post_init__(self):
        super().__post_init__()
        self._none_color("fill_color")
        self._none_color("stroke_color")

    def _generate_contours(self) -> VertexContours:
        """Generate ellipse contours

        Returns VertexContours with a single elliptical outer contour, no  vertex_loops .
        """
        assert self._num_vertices is not None
        ellipse = VertexEllipse(
            center=Point2D(0,0),
            rx=self.rx,
            ry=self.ry,
            num_vertices=self._num_vertices,
            start_angle=0.0,
        )

        return VertexContours(outer=ellipse, holes=[])
