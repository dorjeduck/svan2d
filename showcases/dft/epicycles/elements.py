from __future__ import annotations

from dataclasses import replace
import math

from svan2d.component.state.circle import CircleState
from svan2d.component.state.line import LineState
from svan2d.component.state.path import PathState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement import VElement

from fourier import FourierCoefficient, evaluate_epicycles, evaluate_tip


def _epicycle_center_curve(
    coefficients: list[FourierCoefficient],
    index: int,
):
    """Curve function returning the center of epicycle[index] at time t."""

    def curve(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        positions = evaluate_epicycles(coefficients, t, max_index=index)
        c = positions[index]
        return Point2D(c.real, c.imag)

    return curve


def _arm_center_curve(
    coefficients: list[FourierCoefficient],
    index: int,
):
    """Curve function returning the midpoint of arm[index] at time t.

    Arm[index] connects epicycle center[index] to center[index+1].
    """

    def curve(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        positions = evaluate_epicycles(coefficients, t, max_index=index + 1)
        mid = (positions[index] + positions[index + 1]) / 2
        return Point2D(mid.real, mid.imag)

    return curve


def _arm_rotation_func(
    coefficients: list[FourierCoefficient],
    index: int,
):
    """Rotation function returning the arm[index] rotation at time t.

    Computes rotation from the vector between epicycle centers.
    """

    def rotation_func(r1: float, r2: float, t: float) -> float:

        positions = evaluate_epicycles(coefficients, t, max_index=index + 1)
        p1 = positions[index]
        p2 = positions[index + 1]
        vec = p2 - p1
        return math.degrees(math.atan2(vec.imag, vec.real))

    return rotation_func


def _tip_curve(coefficients: list[FourierCoefficient]):
    """Curve function returning the tip (outermost) position at time t."""

    def curve(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        tip = evaluate_tip(coefficients, t)
        return Point2D(tip.real, tip.imag)

    return curve


def create_epicycle_elements(
    coefficients: list[FourierCoefficient],
    num_trail_vertices: int,
    trail_color: Color,
    trail_width: float,
    arm_color: Color,
    arm_width: float,
    arm_opacity: float,
    circle_color: Color,
    circle_width: float,
    circle_min_opacity: float,
    circle_max_opacity: float,
    tip_color: Color,
    tip_radius: float,
) -> list[VElement]:
    """Build all VElements for the epicycle animation.

    Returns:
        List of VElements ready to add to a VScene.
    """
    num_epicycles = len(coefficients)

    # Compute opacity per epicycle (proportional to radius)
    max_radius = coefficients[0].radius
    min_radius = coefficients[-1].radius
    radius_range = max_radius - min_radius if max_radius != min_radius else 1.0

    def circle_opacity(radius: float) -> float:
        frac = (radius - min_radius) / radius_range
        return circle_min_opacity + frac * (circle_max_opacity - circle_min_opacity)

    # Evaluate start/end positions for keystates
    positions_start = evaluate_epicycles(coefficients, 0.0)
    positions_end = evaluate_epicycles(coefficients, 1.0)

    elements: list[VElement] = []

    # --- Orbit circles (2 keystates each, curve function for pos) ---
    for i in range(num_epicycles):
        radius = coefficients[i].radius
        opacity = circle_opacity(radius)

        start_state = CircleState(
            pos=Point2D(positions_start[i].real, positions_start[i].imag),
            radius=radius,
            stroke_color=circle_color,
            stroke_width=circle_width,
            opacity=opacity,
            z_index=-2.0,
        )
        end_state = replace(
            start_state, pos=Point2D(positions_end[i].real, positions_end[i].imag)
        )

        element = (
            VElement()
            .keystate(start_state, at=0.0)
            .transition(
                interpolation_dict={"pos": _epicycle_center_curve(coefficients, i)}
            )
            .keystate(end_state, at=1.0)
        )
        elements.append(element)

    # --- Arms (2 keystates each, rotation function + position curve) ---
    for i in range(num_epicycles):
        radius = coefficients[i].radius

        # Calculate start state with actual rotation and length
        p1_start = positions_start[i]
        p2_start = positions_start[i + 1]
        vec_start = p2_start - p1_start
        rotation_start = math.degrees(math.atan2(vec_start.imag, vec_start.real))
        mid_start = (p1_start + p2_start) / 2

        # Calculate end state with actual rotation
        p1_end = positions_end[i]
        p2_end = positions_end[i + 1]
        vec_end = p2_end - p1_end
        rotation_end = math.degrees(math.atan2(vec_end.imag, vec_end.real))
        mid_end = (p1_end + p2_end) / 2

        start_state = LineState(
            pos=Point2D(mid_start.real, mid_start.imag),
            rotation=rotation_start,
            length=radius,
            stroke_color=arm_color,
            stroke_width=arm_width,
            fill_color=Color.NONE,
            opacity=arm_opacity,
            z_index=-1.0,
        )
        end_state = replace(
            start_state,
            pos=Point2D(mid_end.real, mid_end.imag),
            rotation=rotation_end,
        )

        element = (
            VElement()
            .keystate(start_state, at=0.0)
            .transition(
                interpolation_dict={
                    "pos": _arm_center_curve(coefficients, i),
                    "rotation": _arm_rotation_func(coefficients, i),
                }
            )
            .keystate(end_state, at=1.0)
        )
        elements.append(element)

    # --- Trail (precomputed shape + draw_progress) ---
    trail_element = _create_trail_element(
        coefficients=coefficients,
        num_trail_vertices=num_trail_vertices,
        trail_color=trail_color,
        trail_width=trail_width,
    )
    elements.append(trail_element)

    # --- Tip dot (2 keystates, curve function for pos) ---
    start_tip = evaluate_tip(coefficients, 0.0)
    end_tip = evaluate_tip(coefficients, 1.0)

    start_state = CircleState(
        pos=Point2D(start_tip.real, start_tip.imag),
        radius=tip_radius,
        fill_color=tip_color,
        stroke_color=Color.NONE,
        z_index=2.0,
    )

    end_state = replace(
        start_state,
        pos=Point2D(end_tip.real, end_tip.imag),
    )

    tip_element = (
        VElement()
        .keystate(
            start_state,
            at=0.0,
        )
        .transition(interpolation_dict={"pos": _tip_curve(coefficients)})
        .keystate(
            end_state,
            at=1.0,
        )
    )
    elements.append(tip_element)

    return elements


def _vertices_to_path_string(vertices: list[complex]) -> str:
    """Convert complex vertices to SVG path string."""
    if not vertices:
        return ""

    parts = [f"M {vertices[0].real:.2f},{vertices[0].imag:.2f}"]
    for v in vertices[1:]:
        parts.append(f"L {v.real:.2f},{v.imag:.2f}")
    return " ".join(parts)  # No Z — open path


def _create_trail_element(
    coefficients: list[FourierCoefficient],
    num_trail_vertices: int,
    trail_color: Color,
    trail_width: float,
) -> VElement:
    """Create a trail that draws progressively using draw_commands.

    The full trail shape is precomputed from the Fourier tip positions
    and drawn incrementally via PathState.draw_commands animation (parameter-based).
    """
    vertices: list[complex] = []
    for vert in range(num_trail_vertices):
        t = vert / (num_trail_vertices - 1)
        tip = evaluate_tip(coefficients, t)
        vertices.append(tip)

    path_string = _vertices_to_path_string(vertices)

    def _trail_state(draw_commands: float) -> PathState:
        return PathState(
            pos=Point2D(0, 0),
            data=path_string,
            stroke_color=trail_color,
            stroke_width=trail_width,
            fill_color=Color.NONE,
            draw_commands=draw_commands,
        )

    return (
        VElement()
        .keystate(_trail_state(0.0), at=0.0)
        .transition(easing_dict={"draw_commands": easing.linear})
        .keystate(_trail_state(1.0), at=1.0)
    )
