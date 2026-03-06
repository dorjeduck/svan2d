"""Renderer for vertex-based shapes with multi-contour support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import drawsvg as dw

if TYPE_CHECKING:
    from svan2d.component.state.base_vertex import VertexState
from svan2d.component.renderer.base import Renderer
from svan2d.component.vertex import VertexContours


@dataclass
class _StyleParams:
    """Bundled style parameters extracted from a VertexState for rendering."""

    fill_color: Any
    fill_opacity: float
    fill_gradient: Any
    fill_pattern: Any
    stroke_color: Any
    stroke_opacity: float
    stroke_width: float
    stroke_gradient: Any
    stroke_pattern: Any
    holes_stroke_color: Any
    holes_stroke_opacity: float
    holes_stroke_width: float
    has_fill: bool
    has_stroke: bool

    @classmethod
    def from_state(cls, state: VertexState) -> _StyleParams:
        fill_color = getattr(state, "fill_color", None)
        fill_opacity = getattr(state, "fill_opacity", 1)
        fill_gradient = getattr(state, "fill_gradient", None)
        fill_pattern = getattr(state, "fill_pattern", None)
        stroke_color = getattr(state, "stroke_color", None)
        stroke_opacity = getattr(state, "stroke_opacity", 1)
        stroke_width = getattr(state, "stroke_width", 0)
        stroke_gradient = getattr(state, "stroke_gradient", None)
        stroke_pattern = getattr(state, "stroke_pattern", None)

        has_fill = bool(
            (fill_pattern or fill_gradient or fill_color)
            and getattr(state, "fill_opacity", 1) > 0
        )
        has_stroke = bool(
            (stroke_pattern or stroke_gradient or stroke_color)
            and stroke_width > 0
            and getattr(state, "stroke_opacity", 1) > 0
        )

        return cls(
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            fill_gradient=fill_gradient,
            fill_pattern=fill_pattern,
            stroke_color=stroke_color,
            stroke_opacity=stroke_opacity,
            stroke_width=stroke_width,
            stroke_gradient=stroke_gradient,
            stroke_pattern=stroke_pattern,
            holes_stroke_color=getattr(state, "holes_stroke_color", stroke_color),
            holes_stroke_opacity=getattr(state, "holes_stroke_opacity", stroke_opacity),
            holes_stroke_width=getattr(state, "holes_stroke_width", stroke_width),
            has_fill=has_fill,
            has_stroke=has_stroke,
        )


class VertexRenderer(Renderer):
    """Renderer for vertex-based shapes with multi-contour support

    Handles both open and closed shapes, with special logic for fill behavior:
    - Open shapes (lines): No fill, only stroke
    - Closed shapes: Both fill and stroke
    - Shapes with  holes : Uses SVG masks for proper rendering during morphing
    - During morphing: Fill fades in/out smoothly

    The key Manim-inspired feature: when morphing from open to closed,
    we implicitly connect the endpoints for fill determination without
    drawing that connecting line.

    Hole rendering strategy:
    - Uses SVG masks (essential for morphing between different hole configurations)
    - Hole strokes rendered separately at normal width
    """

    def _render_core(  # type: ignore[override]
        self, state: VertexState, drawing: dw.Drawing | None = None
    ) -> dw.Group:
        """Render the vertex-based shape."""
        contours = state.get_contours()

        if not contours.outer.vertices:
            return dw.Group()

        group = dw.Group()
        style = _StyleParams.from_state(state)

        if contours.has_holes:
            self._render_with_holes(group, contours, style, state, drawing)
        else:
            vertices_are_closed = self._check_closed(contours.outer.vertices)
            self._render_simple(
                group, contours.outer.vertices, vertices_are_closed,
                style, state, drawing,
            )

        return group

    def _check_closed(self, vertices) -> bool:
        """Check if vertices form a closed shape"""
        if len(vertices) < 2:
            return False

        first_vertex = vertices[0]
        last_vertex = vertices[-1]

        distance = last_vertex.distance_to(first_vertex)

        return distance < 1.0  # Tolerance of 1 pixel

    def _render_simple(
        self,
        group: dw.Group,
        vertices,
        vertices_are_closed: bool,
        style: _StyleParams,
        state: VertexState,
        drawing: dw.Drawing | None,
    ):
        """Render a simple shape without holes."""
        first_vertex = vertices[0]

        if style.has_fill:
            fill_path = self._make_fill_path(style, drawing)
            fill_path.M(first_vertex.x, first_vertex.y)
            for v in vertices[1:]:
                fill_path.L(v.x, v.y)
            fill_path.Z()
            group.append(fill_path)

        if style.has_stroke:
            # Apply draw_progress: limit vertices to a fraction of the polyline
            draw_progress = getattr(state, "draw_progress", 1.0)
            if draw_progress < 1.0:
                n = max(int(draw_progress * len(vertices)), 1)
                stroke_vertices = vertices[:n]
            else:
                stroke_vertices = vertices

            stroke_kwargs = self._stroke_kwargs(state)
            stroke_path = self._make_stroke_path(
                style, stroke_kwargs, drawing,
            )

            stroke_path.M(stroke_vertices[0].x, stroke_vertices[0].y)
            for v in stroke_vertices[1:]:
                stroke_path.L(v.x, v.y)

            if vertices_are_closed and draw_progress >= 1.0:
                stroke_path.Z()

            group.append(stroke_path)

    def _render_with_holes(
        self,
        group: dw.Group,
        contours: VertexContours,
        style: _StyleParams,
        state: VertexState,
        drawing: dw.Drawing | None,
    ):
        """Render a shape with vertex loops using SVG masks.

        Strategy:
        1. Create a mask with white outer contour and black holes
        2. Add mask to drawing's defs section
        3. Apply mask to fill via mask attribute
        4. Render strokes separately
        """
        import random

        mask_id = f"hole-mask-{random.randint(1000000, 9999999)}"
        outer_verts = contours.outer.vertices

        # Create mask
        mask = dw.Mask(id=mask_id)

        # Mask: White outer contour (reveals)
        outer_mask_path = dw.Path(fill="white")
        if outer_verts:
            outer_mask_path.M(outer_verts[0].x, outer_verts[0].y)
            for v in outer_verts[1:]:
                outer_mask_path.L(v.x, v.y)
            outer_mask_path.Z()
        mask.append(outer_mask_path)

        # Mask: Black vertex loops (hides)
        for hole in contours.holes:
            hole_mask_path = dw.Path(fill="black")
            hole_verts = hole.vertices
            if hole_verts:
                hole_mask_path.M(hole_verts[0].x, hole_verts[0].y)
                for v in hole_verts[1:]:
                    hole_mask_path.L(v.x, v.y)
                hole_mask_path.Z()
            mask.append(hole_mask_path)

        if drawing is not None:
            drawing.append_def(mask)

        # Render fill with mask applied
        if style.has_fill:
            fill_path = self._make_fill_path(style, drawing, mask_id=mask_id)
            fill_path.M(outer_verts[0].x, outer_verts[0].y)
            for v in outer_verts[1:]:
                fill_path.L(v.x, v.y)
            fill_path.Z()
            group.append(fill_path)

        # Render strokes (not affected by mask)
        if style.has_stroke:
            stroke_kwargs = self._stroke_kwargs(state)

            # Outer stroke
            outer_stroke_path = self._make_stroke_path(
                style, stroke_kwargs, drawing,
            )
            outer_stroke_path.M(outer_verts[0].x, outer_verts[0].y)
            for v in outer_verts[1:]:
                outer_stroke_path.L(v.x, v.y)
            outer_stroke_path.Z()
            group.append(outer_stroke_path)

            # Hole strokes — double width because mask hides half
            for hole in contours.holes:
                hole_verts = hole.vertices
                if hole_verts:
                    hole_stroke_path = dw.Path(
                        fill="none",
                        stroke=style.holes_stroke_color.to_rgb_string(),
                        stroke_opacity=style.holes_stroke_opacity,
                        stroke_width=style.holes_stroke_width * 2,
                        mask=f"url(#{mask_id})",
                        **stroke_kwargs,
                    )
                    hole_stroke_path.M(hole_verts[0].x, hole_verts[0].y)
                    for v in hole_verts[1:]:
                        hole_stroke_path.L(v.x, v.y)
                    hole_stroke_path.Z()
                    group.append(hole_stroke_path)

    # ------------------------------------------------------------------
    # Shared path construction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _stroke_kwargs(state: VertexState) -> dict:
        """Extract extra stroke keyword arguments from state."""
        kwargs: dict = {}
        if hasattr(state, "stroke_linecap") and state.stroke_linecap is not None:
            kwargs["stroke_linecap"] = state.stroke_linecap
        if getattr(state, "non_scaling_stroke", False):
            kwargs["vector_effect"] = "non-scaling-stroke"
        return kwargs

    @staticmethod
    def _make_fill_path(
        style: _StyleParams,
        drawing: dw.Drawing | None,
        *,
        mask_id: str | None = None,
    ) -> dw.Path:
        """Create a fill path element from style params."""
        extra: dict = {}
        if mask_id:
            extra["mask"] = f"url(#{mask_id})"

        if style.fill_pattern:
            return dw.Path(fill=style.fill_pattern.to_drawsvg(drawing), stroke="none", **extra)
        if style.fill_gradient:
            return dw.Path(fill=style.fill_gradient.to_drawsvg(), stroke="none", **extra)
        return dw.Path(
            fill=style.fill_color.to_rgb_string(),
            fill_opacity=style.fill_opacity,
            stroke="none",
            **extra,
        )

    @staticmethod
    def _make_stroke_path(
        style: _StyleParams,
        extra_kwargs: dict,
        drawing: dw.Drawing | None,
    ) -> dw.Path:
        """Create a stroke path element from style params."""
        if style.stroke_pattern:
            return dw.Path(
                fill="none",
                stroke=style.stroke_pattern.to_drawsvg(drawing),
                stroke_width=style.stroke_width,
                **extra_kwargs,
            )
        if style.stroke_gradient:
            return dw.Path(
                fill="none",
                stroke=style.stroke_gradient.to_drawsvg(),
                stroke_width=style.stroke_width,
                **extra_kwargs,
            )
        return dw.Path(
            fill="none",
            stroke=style.stroke_color.to_rgb_string(),
            stroke_opacity=style.stroke_opacity,
            stroke_width=style.stroke_width,
            **extra_kwargs,
        )
