"""Shared pendulum element construction for all variants.

Each variant just computes a layout (list of PendulumSpec) and calls
create_pendulums() to build the VElements.
"""

import math
from dataclasses import dataclass, replace

from physics import lookup_cycle, precompute_pendulum_cycle

from svan2d import Color, Point2D, VElement
from svan2d.primitive.state.circle import CircleState
from svan2d.primitive.state.line import LineState


@dataclass(frozen=True)
class PendulumSpec:
    """Layout specification for a single pendulum."""

    pivot: Point2D
    orientation: float  # radians — direction the pendulum hangs (π/2 = down)
    freq: float


def _compute_effective_t(
    t: float, freq: float, quantize_freq: bool,
) -> float:
    """Apply quantize_freq time clamping."""
    if quantize_freq:
        max_full = int(freq)
        if max_full > 0:
            active_frac = max_full / freq
            return min(t, active_frac)
    return t


def _make_bob_pos_fn(
    pivot: Point2D,
    arm_length: float,
    orientation: float,
    freq: float,
    cycle: list[float],
    quantize_freq: bool,
):
    cos_a = math.cos(orientation)
    sin_a = math.sin(orientation)

    def interpolate(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        effective_t = _compute_effective_t(t, freq, quantize_freq)
        theta = lookup_cycle(cycle, freq * effective_t)
        dx = arm_length * (math.cos(theta) * cos_a - math.sin(theta) * sin_a)
        dy = arm_length * (math.cos(theta) * sin_a + math.sin(theta) * cos_a)
        return Point2D(pivot.x + dx, pivot.y + dy)

    return interpolate


def _make_arm_state_fn(
    pivot: Point2D,
    arm_length: float,
    orientation: float,
    freq: float,
    cycle: list[float],
    quantize_freq: bool,
):
    cos_a = math.cos(orientation)
    sin_a = math.sin(orientation)

    def interpolate(
        start_state: LineState, end_state: LineState, t: float
    ) -> LineState:
        effective_t = _compute_effective_t(t, freq, quantize_freq)
        theta = lookup_cycle(cycle, freq * effective_t)
        dx = arm_length * (math.cos(theta) * cos_a - math.sin(theta) * sin_a)
        dy = arm_length * (math.cos(theta) * sin_a + math.sin(theta) * cos_a)
        end_x = pivot.x + dx
        end_y = pivot.y + dy
        cx = (pivot.x + end_x) / 2
        cy = (pivot.y + end_y) / 2
        rotation = math.degrees(math.atan2(end_y - pivot.y, end_x - pivot.x))
        return replace(start_state, pos=Point2D(cx, cy), rotation=rotation)

    return interpolate


def create_pendulums(
    specs: list[PendulumSpec],
    arm_length: float,
    bob_radius: float,
    max_angle: float,
    arm_color: str,
    arm_width: float,
    bob_color_start: Color,
    bob_color_end: Color,
    quantize_freq: bool = False,
) -> list[VElement]:
    """Create bob and arm VElements from a list of PendulumSpecs."""
    max_angle_rad = math.radians(max_angle)
    cycle = precompute_pendulum_cycle(max_angle_rad)

    elements: list[VElement] = []
    count = len(specs)

    for i, spec in enumerate(specs):
        frac = i / (count - 1) if count > 1 else 0.0
        bob_color = bob_color_start.interpolate(bob_color_end, frac)

        cos_a = math.cos(spec.orientation)
        sin_a = math.sin(spec.orientation)

        # --- Bob ---
        bob_rest = Point2D(
            spec.pivot.x + arm_length * cos_a,
            spec.pivot.y + arm_length * sin_a,
        )
        bob_state = CircleState(
            pos=bob_rest,
            radius=bob_radius,
            fill_color=bob_color,
        )

        bob = (
            VElement()
            .keystate(bob_state, at=0.0)
            .transition(
                interpolation_dict={
                    "pos": _make_bob_pos_fn(
                        spec.pivot, arm_length, spec.orientation,
                        spec.freq, cycle, quantize_freq,
                    )
                }
            )
            .keystate(bob_state, at=1.0)
        )

        # --- Arm ---
        arm_center = Point2D(
            spec.pivot.x + arm_length / 2 * cos_a,
            spec.pivot.y + arm_length / 2 * sin_a,
        )
        arm_rotation = math.degrees(spec.orientation)
        arm_state = LineState(
            pos=arm_center,
            length=arm_length,
            rotation=arm_rotation,
            stroke_color=arm_color,
            stroke_width=arm_width,
        )

        arm = (
            VElement()
            .keystate(arm_state, at=0.0)
            .transition(
                state_interpolation=_make_arm_state_fn(
                    spec.pivot, arm_length, spec.orientation,
                    spec.freq, cycle, quantize_freq,
                )
            )
            .keystate(arm_state, at=1.0)
        )

        elements.append(arm)
        elements.append(bob)

    return elements
