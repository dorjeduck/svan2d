"""Astroid state implementation - star-like shape with inward-curving cusps"""

from __future__ import annotations
from dataclasses import dataclass

from svan2d.core.point2d import Point2D

from .base import State
from .base_vertex import VertexState
from svan2d.component.vertex import VertexContours, VertexAstroid
from svan2d.component.registry import renderer
from svan2d.component.renderer.astroid import AstroidRenderer
from svan2d.transition import easing


@renderer(AstroidRenderer)
@dataclass(frozen=True)
class AstroidState(VertexState):
    """State class for astroid elements - star-like shape with inward-curving cusps

    An astroid is a star-like shape formed by connecting cusp points (sharp tips)
    with inward-bending circular arcs. The classic astroid has 4 cusps, but this
    implementation supports any number.

    The shape gets its distinctive appearance from the concave curves between
    the pointed cusps, creating an elegant star-burst or flower-like pattern.
    """

    radius: float = 50
    num_cusps: int = 4  # Number of pointed tips (4 for classic astroid)
    curvature: float = 0.7  # How much arcs bend inward (0-1)

    # Default easing functions for each field
    DEFAULT_EASING = {
        **State.DEFAULT_EASING,
        "radius": easing.in_out,
        "num_cusps": easing.step,  # Discrete values, no smooth interpolation
        "curvature": easing.in_out,
    }

    def _generate_contours(self) -> VertexContours:
        """Generate astroid contours

        Returns VertexContours with:
        - Outer: astroid shape (counter-clockwise)
        -  vertex_loops : none (astroids don't have  vertex_loops )
        """
        # Generate astroid shape
        astroid = VertexAstroid(
            center=Point2D(),
            radius=self.radius,
            num_cusps=self.num_cusps,
            curvature=self.curvature,
            num_vertices=self._num_vertices,
        )

        return VertexContours(outer=astroid, holes=[])
