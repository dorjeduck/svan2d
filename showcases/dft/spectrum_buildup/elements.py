"""VElement construction for the spectrum buildup showcase.

Each stage draws one full revolution with an increasing number of
Fourier coefficients, showing the approximation sharpening over time.

Demonstrates svan2d animation features:
- draw_commands: progressive path drawing via PathState.draw_commands (parameter-based)
- Curve functions: custom Fourier-based trajectory for tip dot position
- Normalized time: all animations work with at= times (0.0 to 1.0)
- Easing: smooth opacity fade with easing.in_quad
"""

from __future__ import annotations
from typing import List

from svan2d.component.state.base import State
from svan2d.component.state.circle import CircleState
from svan2d.component.state.path import PathState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement import VElement
from svan2d.transition import easing

from fourier import FourierCoefficient, evaluate_tip


def _fourier_curve(coefficients: list[FourierCoefficient]):
    """Create a curve function that follows the Fourier path.

    Returns a curve function with signature (p1, p2, t) -> Point2D
    that evaluates the Fourier tip position at parameter t.
    The p1/p2 arguments are ignored — the trajectory is fully
    determined by the Fourier coefficients.
    """

    def curve(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        tip = evaluate_tip(coefficients, t)
        return Point2D(tip.real, tip.imag)

    return curve


def create_buildup_elements(
    coefficients: list[FourierCoefficient],
    stages: list[int],
    num_trail_vertices: int,
    color_start: Color,
    color_end: Color,
    trail_width: float,
    tip_color: Color,
    tip_radius: float,
    label_color: Color,
    label_font_size: float,
    label_y: float,
    fade_duration: float,
) -> list[VElement]:
    """Build VElements for the spectrum buildup animation.

    Args:
        fade_duration: Normalized fade duration (e.g., 0.3 means 30% of timeline)

    Returns:
        List of VElements: one trail per stage + one tip dot + labels.
    """
    num_stages = len(stages)

    elements: list[VElement] = []

    # --- Trail elements (one per stage, using draw_commands) ---
    for stage_idx, num_coeffs in enumerate(stages):
        stage_coeffs = coefficients[:num_coeffs]
        stage_t = stage_idx / max(num_stages - 1, 1)
        trail_color = color_start.interpolate(color_end, stage_t)

        trail = _create_stage_trail(
            coefficients=stage_coeffs,
            stage_idx=stage_idx,
            num_trail_vertices=num_trail_vertices,
            trail_color=trail_color,
            trail_width=trail_width,
            fade_duration=fade_duration,
            num_stages=num_stages,
        )
        elements.append(trail)

    # --- Tip dot (one VElement, Fourier curve per stage) ---
    tip = _create_tip_element(
        coefficients=coefficients,
        stages=stages,
        tip_color=tip_color,
        tip_radius=tip_radius,
    )
    elements.append(tip)

    # --- Labels ---
    line_spacing = label_font_size * 1.4
    label_base = dict(
        font_family="Helvetica",
        fill_color=label_color,
        z_index=3.0,
    )

    # "Fourier" — static
    state = TextState(
        pos=Point2D(0, label_y),
        text="Fourier",
        font_size=label_font_size,
        **label_base,
    )
    elements.append(VElement().keystates([state, state]))

    state = TextState(
        pos=Point2D(0, label_y + line_spacing),
        text="Coefficients:",
        font_size=label_font_size,
        **label_base,
    )
    elements.append(VElement().keystates([state, state]))

    # Number — keystates at stage boundaries
    number_element = _create_number_label(
        stages=stages,
        label_y=label_y + line_spacing * 2,
        label_font_size=label_font_size,
        label_base=label_base,
    )
    elements.append(number_element)

    return elements


def _vertices_to_path_string(vertices: list[complex]) -> str:
    """Convert complex vertices to SVG path string."""
    if not vertices:
        return ""

    parts = [f"M {vertices[0].real:.2f},{vertices[0].imag:.2f}"]
    for v in vertices[1:]:
        parts.append(f"L {v.real:.2f},{v.imag:.2f}")
    return " ".join(parts)  # No Z — open path


def _create_stage_trail(
    coefficients: list[FourierCoefficient],
    stage_idx: int,
    num_trail_vertices: int,
    trail_color: Color,
    trail_width: float,
    fade_duration: float,
    num_stages: int,
) -> VElement:
    """Create a trail that draws in during its stage and fades out after.

    Uses PathState with draw_commands: 2 keystates per stage for the draw-in,
    plus 2 more for the fade-out. The complete shape path is computed
    once and animated via draw_commands from 0→1.
    """
    is_last_stage = stage_idx == num_stages - 1

    # Stage occupies 1/num_stages of the timeline
    stage_duration = 1.0 / num_stages
    t_stage_start = stage_idx * stage_duration
    t_stage_end = min((stage_idx + 1) * stage_duration, 1.0)

    # Precompute the complete loop vertices
    complete_vertices: list[complex] = []
    for v_idx in range(num_trail_vertices):
        t_dft = v_idx / num_trail_vertices
        pos = evaluate_tip(coefficients, t_dft)
        complete_vertices.append(pos)
    complete_vertices.append(complete_vertices[0])  # close the loop

    path_string = _vertices_to_path_string(complete_vertices)

    def _trail_state(draw_commands: float, opacity: float) -> PathState:
        return PathState(
            pos=Point2D(0, 0),
            data=path_string,
            stroke_color=trail_color,
            stroke_width=trail_width,
            fill_color=Color.NONE,
            draw_commands=draw_commands,
            opacity=opacity,
        )

    element = VElement().keystate(_trail_state(0.0, 1.0), at=t_stage_start)
    element = element.keystate(_trail_state(1.0, 1.0), at=t_stage_end)

    if not is_last_stage:
        # Fade out after stage ends
        t_fade_end = min(t_stage_end + fade_duration, 1.0)
        element = element.transition(easing_dict={"opacity": easing.linear})
        element = element.keystate(_trail_state(1.0, 0.0), at=t_fade_end)

    return element


def _create_tip_element(
    coefficients: list[FourierCoefficient],
    stages: list[int],
    tip_color: Color,
    tip_radius: float,
) -> VElement:
    """Create the tip dot element using Fourier curve functions.

    Each stage uses a custom curve function that traces the Fourier path,
    so only 2 keystates per stage are needed (start + end positions).
    At stage boundaries, dual-state keystates handle the instant position
    switch between different coefficient sets.
    """
    num_stages = len(stages)
    stage_duration = 1.0 / num_stages
    element = VElement()

    def _tip_state(pos: complex) -> CircleState:
        return CircleState(
            pos=Point2D(pos.real, pos.imag),
            radius=tip_radius,
            fill_color=tip_color,
            stroke_color=Color.NONE,
            z_index=2.0,
        )

    prev_end_pos: complex = 0j
    for stage_idx, num_coeffs in enumerate(stages):
        stage_coeffs = coefficients[:num_coeffs]
        t_start = stage_idx * stage_duration

        tip_start_pos = evaluate_tip(stage_coeffs, 0.0)
        tip_end_pos = evaluate_tip(stage_coeffs, 1.0)
        start_state = _tip_state(tip_start_pos)
        end_state = _tip_state(tip_end_pos)

        if stage_idx == 0:
            element = element.keystate(start_state, at=0.0)
        else:
            # Dual-state at boundary: incoming from previous end, outgoing to new start
            element = element.keystate(
                [_tip_state(prev_end_pos), start_state], at=t_start
            )

        element = element.transition(
            interpolation_dict={"pos": _fourier_curve(stage_coeffs)}
        )

        if stage_idx == num_stages - 1:
            element = element.keystate(end_state, at=1.0)

        prev_end_pos = tip_end_pos

    return element


def _create_number_label(
    stages: list[int],
    label_y: float,
    label_font_size: float,
    label_base: dict,
) -> VElement:

    num_stages = len(stages)
    stage_duration = 1.0 / num_stages

    def _num_state(num_coeffs: int) -> TextState:
        return TextState(
            pos=Point2D(0, label_y),
            text=str(num_coeffs),
            font_size=label_font_size,
            **label_base,
        )

    states: List[TextState] = [_num_state(num_coeff) for num_coeff in stages]

    element = VElement()

    for idx in range(len(stages)):

        if idx == 0:
            element = element.keystate(state=states[0], at=0)
            element = element.keystate(state=[states[0], states[1]], at=stage_duration)
        elif idx == len(stages) - 1:
            element = element.keystate(states[-1], at=1)
        else:
            element = element.keystate(
                [states[idx], states[idx + 1]], at=(idx + 1) * stage_duration
            )

    return element
