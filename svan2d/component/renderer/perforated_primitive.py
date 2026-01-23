"""Perforated primitive renderer - SVG primitive-based for static/keystate rendering"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

import drawsvg as dw

from svan2d.core.color import Color

from .base import Renderer

if TYPE_CHECKING:
    from ..state.perforated.base import (
        Astroid,
        Circle,
        Ellipse,
        PerforatedVertexState,
        Polygon,
        Rectangle,
        Shape,
        Star,
    )
from svan2d.core.point2d import Point2D


class PerforatedPrimitiveRenderer(Renderer):
    """Renderer for perforated shape elements using SVG primitives

    Works with all PerforatedXState classes (PerforatedCircle, PerforatedStar, etc.)
    by converting their vertex-based outer contours to SVG paths.

    Uses evenodd fill-rule with SVG paths for clean, high-quality rendering.
    Renders any outer shape with multiple vertex loops of any shape at different
    positions, sizes, and rotations.

    This is used for static rendering and at keystate endpoints (t=0, t=1).
    During morphing (0 < t < 1), the VertexRenderer is used instead to enable
    smooth transitions between different shapes.
    """

    def _render_core(  # type: ignore[override]
        self, state: "PerforatedVertexState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Group:
        """Render perforated shape using SVG path primitives with evenodd fill-rule"""

        group = dw.Group()

        # Get stroke values with defaults for Optional fields
        stroke_width = state.stroke_width or 0
        stroke_opacity = state.stroke_opacity or 0
        holes_stroke_width = state.holes_stroke_width or 0
        holes_stroke_opacity = state.holes_stroke_opacity or 0
        holes_fill_opacity = state.holes_fill_opacity or 0

        # Create a path that defines the perforated shape using even-odd fill rule
        fill_path = dw.Path(
            fill=state.fill_color.to_rgb_string() if state.fill_color else "none",
            fill_opacity=state.fill_opacity,
            fill_rule="evenodd",
            stroke="none",
        )

        outer_stroke_path = dw.Path(
            fill="none",
            stroke=(
                state.stroke_color.to_rgb_string()
                if state.stroke_color and stroke_width > 0
                else "none"
            ),
            stroke_width=(
                stroke_width
                if state.stroke_color and stroke_width > 0
                else 0
            ),
            stroke_opacity=(
                stroke_opacity
                if state.stroke_color and stroke_width > 0
                else 0
            ),
            stroke_linejoin="round",
            stroke_linecap="round",
        )

        hole_stroke_path = dw.Path(
            fill=(
                state.holes_fill_color.to_rgb_string()
                if state.holes_fill_color
                else "none"
            ),
            fill_opacity=holes_fill_opacity,
            stroke=(
                state.holes_stroke_color.to_rgb_string()
                if state.holes_stroke_color
                and holes_stroke_width > 0
                else "none"
            ),
            stroke_width=(
                holes_stroke_width
                if state.holes_stroke_color
                and holes_stroke_width > 0
                else 0
            ),
            stroke_opacity=(
                holes_stroke_opacity
                if state.holes_stroke_color
                and holes_stroke_width > 0
                else 0
            ),
            stroke_linejoin="round",
            stroke_linecap="round",
        )

        # Draw outer shape (clockwise for outer boundary)
        # Get the outer contour from the state's _generate_outer_contour() method
        outer_contour = state._generate_outer_contour()

        self._add_vertex_loop_to_path(fill_path, outer_contour.vertices, clockwise=True)

        # Draw hole shapes (counter-clockwise - creates vertex loops due to even-odd rule)
        for hole_shape in state.holes:
            self._add_shape_to_path(fill_path, hole_shape, clockwise=False)

        group.append(fill_path)

        if stroke_width > 0 and stroke_opacity > 0:
            self._add_vertex_loop_to_path(outer_stroke_path, outer_contour.vertices)
            group.append(outer_stroke_path)

        if (
            holes_stroke_width > 0
            and holes_stroke_opacity > 0
        ) or (
            state.holes_fill_color != Color.NONE
            and holes_fill_opacity > 0
        ):
            for hole_shape in state.holes:
                self._add_shape_to_path(hole_stroke_path, hole_shape)
            group.append(hole_stroke_path)

        return group

    def _add_vertex_loop_to_path(
        self, path: dw.Path, vertices: list, clockwise: bool = True
    ):
        """Add a vertex loop to the path

        Args:
            path: The path to add vertices to
            vertices: List of (x, y) tuples
            clockwise: If True, draw clockwise; if False, reverse order
        """
        if not vertices or len(vertices) < 2:
            return

        verts = list(vertices)
        if not clockwise:
            verts = verts[::-1]

        # Start at first vertex
        path.M(verts[0].x, verts[0].y)

        # Draw lines to remaining vertices
        for vertex in verts[
            1:-1
        ]:  # Skip last vertex (should equal first for closed loop)
            path.L(vertex.x, vertex.y)

        path.Z()

    def _add_shape_to_path(self, path: dw.Path, shape: Shape, clockwise: bool = True):
        """Add a shape to the path by working directly with the Shape object

        Args:
            path: The path to add the shape to
            shape: Shape object (Circle, Ellipse, Rectangle, etc.)
            clockwise: If True, draw clockwise; if False, draw counter-clockwise
        """
        # shape.pos is guaranteed non-None after Shape.__post_init__
        assert shape.pos is not None
        center = shape.pos

        if isinstance(shape, Circle):
            self._add_circle(path, center, shape.radius, clockwise)

        elif isinstance(shape, Ellipse):
            self._add_ellipse(
                path, center, shape.rx, shape.ry, shape.rotation, clockwise
            )

        elif isinstance(shape, Rectangle):
            self._add_rectangle(
                path,
                center,
                shape.width,
                shape.height,
                shape.rotation,
                clockwise,
            )

        elif isinstance(shape, Polygon):
            self._add_polygon(
                path,
                center,
                shape.radius,
                shape.num_sides,
                shape.rotation,
                clockwise,
            )

        elif isinstance(shape, Star):
            self._add_star(
                path,
                center,
                shape.outer_radius,
                shape.inner_radius,
                shape.num_points,
                shape.rotation,
                clockwise,
            )

        elif isinstance(shape, Astroid):
            self._add_astroid(
                path,
                center,
                shape.radius,
                shape.num_cusps,
                shape.curvature,
                shape.rotation,
                clockwise,
            )

        else:
            raise ValueError(f"Unsupported shape type: {type(shape).__name__}")

    def _add_circle(
        self, path: dw.Path, center: Point2D, radius: float, clockwise: bool
    ):
        """Add a circle to path using arc commands"""
        path.M(center.x + radius, center.y)
        sweep_flag = 1 if clockwise else 0
        path.A(radius, radius, 0, 0, sweep_flag, center.x - radius, center.y)
        path.A(radius, radius, 0, 0, sweep_flag, center.x + radius, center.y)
        path.Z()

    def _add_rectangle(
        self,
        path: dw.Path,
        center: Point2D,
        width: float,
        height: float,
        rotation: float,
        clockwise: bool,
    ):
        """Add a rectangle to path"""
        half_w, half_h = width / 2, height / 2
        corners = [
            (-half_w, -half_h),
            (half_w, -half_h),
            (half_w, half_h),
            (-half_w, half_h),
        ]

        # Apply rotation if specified
        if rotation != 0:
            angle_rad = math.radians(rotation)
            cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
            corners = [
                (x * cos_a - y * sin_a + center.x, x * sin_a + y * cos_a + center.y)
                for x, y in corners
            ]
        else:
            corners = [(x + center.x, y + center.y) for x, y in corners]

        # Draw rectangle
        if not clockwise:
            corners = corners[::-1]  # Reverse for counter-clockwise

        path.M(corners[0][0], corners[0][1])
        for corner in corners[1:]:
            path.L(corner[0], corner[1])
        path.Z()

    def _add_ellipse(
        self,
        path: dw.Path,
        center: Point2D,
        rx: float,
        ry: float,
        rotation: float,
        clockwise: bool,
    ):
        """Add an ellipse to path using arc commands"""
        if clockwise:
            # Clockwise: start right, go down, left, up, back to right
            path.M(center.x + rx, center.y)
            path.A(rx, ry, rotation, 0, 1, center.x, center.y + ry)
            path.A(rx, ry, rotation, 0, 1, center.x - rx, center.y)
            path.A(rx, ry, rotation, 0, 1, center.x, center.y - ry)
            path.A(rx, ry, rotation, 0, 1, center.x + rx, center.y)
        else:
            # Counter-clockwise: start right, go up, left, down, back to right
            path.M(center.x + rx, center.y)
            path.A(rx, ry, rotation, 0, 0, center.x, center.y - ry)
            path.A(rx, ry, rotation, 0, 0, center.x - rx, center.y)
            path.A(rx, ry, rotation, 0, 0, center.x, center.y + ry)
            path.A(rx, ry, rotation, 0, 0, center.x + rx, center.y)
        path.Z()

    def _add_polygon(
        self,
        path: dw.Path,
        center: Point2D,
        size: float,
        num_sides: int,
        rotation: float,
        clockwise: bool,
    ):
        """Add a regular polygon to path"""
        corners = []
        for i in range(num_sides):
            angle = math.radians(i * (360 / num_sides) - 90 + rotation)
            x = center.x + size * math.cos(angle)
            y = center.y + size * math.sin(angle)
            corners.append(Point2D(x, y))

        if not clockwise:
            corners = corners[::-1]

        path.M(corners[0].x, corners[0].y)
        for corner in corners[1:]:
            path.L(corner.x, corner.y)
        path.Z()

    def _add_star(
        self,
        path: dw.Path,
        center: Point2D,
        outer_radius: float,
        inner_radius: float,
        num_points: int,
        rotation: float,
        clockwise: bool,
    ):
        """Add a star to path with alternating outer and inner vertices"""
        corners = []
        for i in range(num_points * 2):
            angle = math.radians(i * (360 / (num_points * 2)) - 90 + rotation)
            # Alternate between outer and inner radius
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            corners.append(Point2D(x, y))

        if not clockwise:
            corners = corners[::-1]

        path.M(corners[0].x, corners[0].y)
        for corner in corners[1:]:
            path.L(corner.x, corner.y)
        path.Z()

    def _add_astroid(
        self,
        path: dw.Path,
        center: Point2D,
        radius: float,
        num_cusps: int,
        curvature: float,
        rotation: float,
        clockwise: bool,
    ):
        """Add an astroid to path using quadratic Bezier curves"""
        # Calculate cusp positions (the pointed tips)
        cusps = []
        for i in range(num_cusps):
            angle = math.radians(i * (360 / num_cusps) - 90 + rotation)
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            cusps.append(Point2D(x, y))

        if not clockwise:
            cusps = cusps[::-1]

        # Start at first cusp
        path.M(cusps[0].x, cusps[0].y)

        # Draw curves connecting cusps
        for i in range(num_cusps):
            start_cusp = cusps[i]
            end_cusp = cusps[(i + 1) % num_cusps]

            # Calculate control point for inward-bending curve
            mid_x = (start_cusp.x + end_cusp.x) / 2
            mid_y = (start_cusp.y + end_cusp.y) / 2

            # Pull control point toward center based on curvature
            control_x = mid_x + (center.x - mid_x) * curvature
            control_y = mid_y + (center.y - mid_y) * curvature

            # Draw quadratic Bezier curve to next cusp
            path.Q(control_x, control_y, end_cusp.x, end_cusp.y)

        path.Z()
