"""Polygon renderer implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import drawsvg as dw

from .base import Renderer

if TYPE_CHECKING:
    from ..state.polygon import PolygonState


class PolygonRenderer(Renderer):
    """Renderer for polygon elements."""

    def _render_core(
        self, state: "PolygonState", drawing: dw.Drawing | None = None
    ) -> dw.Lines:
        """Render regular polygon as a closed SVG Lines element.

        Args:
            state: PolygonState to render
        """
        import math

        # Generate corner points only
        corners = []
        for i in range(state.num_sides):
            angle = (i / state.num_sides) * 2 * math.pi - math.pi / 2
            x = state.size * math.cos(angle)
            y = state.size * math.sin(angle)
            corners.extend([x, y])

        # Build kwargs
        lines_kwargs = {"close": True}
        self._set_fill_and_stroke_kwargs(state, lines_kwargs, drawing)

        return dw.Lines(*corners, **lines_kwargs)
