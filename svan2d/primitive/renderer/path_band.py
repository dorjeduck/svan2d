"""PathBand renderer: emits a group of line segments with per-segment styling."""

from __future__ import annotations

from typing import TYPE_CHECKING

import drawsvg as dw

from .base import Renderer

if TYPE_CHECKING:
    from ..state.path_band import PathBandState


class PathBandRenderer(Renderer):
    """Renderer for PathBandState.

    Emits a <g> containing one <line> per segment. Per-segment stroke_opacity
    and stroke_width (when provided) override the shared values on the state.
    """

    def _render_core(
        self, state: "PathBandState", drawing: dw.Drawing | None = None
    ) -> dw.Group:
        shared: dict = {
            "stroke_linecap": state.stroke_linecap,
            "stroke_linejoin": state.stroke_linejoin,
        }
        self._set_fill_and_stroke_kwargs(state, shared, drawing)
        shared["fill"] = "none"
        shared.pop("fill_opacity", None)

        group = dw.Group()

        from svan2d.core.color import Color

        opacities = state.stroke_opacities
        widths = state.stroke_widths
        colors = state.stroke_colors

        for i, (a, b) in enumerate(state.segments):
            line_kwargs = dict(shared)
            if colors is not None and i < len(colors):
                c = colors[i]
                if c is not None and c != Color.NONE:
                    line_kwargs["stroke"] = c.to_rgb_string()
            if opacities is not None and i < len(opacities):
                line_kwargs["stroke_opacity"] = opacities[i]
            if widths is not None and i < len(widths):
                line_kwargs["stroke_width"] = widths[i]
            # Cartesian Y-up → SVG Y-down.
            group.append(dw.Line(a.x, -a.y, b.x, -b.y, **line_kwargs))

        return group
