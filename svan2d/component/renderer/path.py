"""Path renderer implementation for custom SVG paths (like zodiac signs)"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import drawsvg as dw

from svan2d.path.svg_path import SVGPath

from .base import Renderer

if TYPE_CHECKING:
    from ..state.path import PathState


class PathRenderer(Renderer):
    """Renderer class for rendering custom SVG path elements"""

    def _render_core(
        self, state: "PathState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Path:
        """Render the renderer's geometry with the given state

        Returns:
            drawsvg Path object
        """
        # Create path with basic attributes

        svg_path_obj = state.data if isinstance(state.data, SVGPath) else SVGPath.from_string(str(state.data))

        # Handle draw_commands (parameter-based, takes priority over draw_progress)
        draw_commands = getattr(state, "draw_commands", 1.0)
        if draw_commands < 1.0:
            # Render only first N commands (parameter-based drawing)
            num_commands = max(int(draw_commands * len(svg_path_obj.commands)), 1)
            partial_commands = svg_path_obj.commands[:num_commands]
            path_d = SVGPath(partial_commands).to_string()
        else:
            path_d = svg_path_obj.to_string()

        # Handle draw_progress via stroke-dasharray/dashoffset (arc-length-based)
        stroke_dasharray = state.stroke_dasharray
        stroke_dashoffset = None

        draw_progress = getattr(state, "draw_progress", 1.0)
        if draw_progress < 1.0 and draw_commands >= 1.0 and state.stroke_width > 0:
            # Only apply draw_progress if draw_commands is not active
            path_length = svg_path_obj.length()
            visible_length = path_length * draw_progress
            stroke_dasharray = f"{visible_length} {path_length}"
            stroke_dashoffset = 0

        path_kwargs = {
            "d": path_d,
            "fill_rule": state.fill_rule,
            "stroke_dasharray": stroke_dasharray,
            "stroke_linecap": state.stroke_linecap,
            "stroke_linejoin": state.stroke_linejoin,
        }

        if stroke_dashoffset is not None:
            path_kwargs["stroke_dashoffset"] = stroke_dashoffset

        self._set_fill_and_stroke_kwargs(state, path_kwargs, drawing)

        return dw.Path(**path_kwargs)
