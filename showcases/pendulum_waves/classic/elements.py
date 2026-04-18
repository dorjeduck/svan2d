"""Element construction for the classic pendulum waves showcase."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from pendulum import PendulumSpec, create_pendulums

from svan2d import Color, Point2D, VElement
from svan2d.primitive.state.line import LineState

ORIENTATION_DOWN = -math.pi / 2


def create_support_bar(
    center_y: float,
    width: float,
    color: str,
    stroke_width: float,
) -> VElement:
    """Create the horizontal support bar."""
    bar_state = LineState(
        pos=Point2D(0, center_y),
        length=width,
        rotation=0,
        stroke_color=color,
        stroke_width=stroke_width,
    )
    return VElement(state=bar_state)


def create_pendulum_elements(
    count: int,
    pivot_y: float,
    arm_length: float,
    bob_radius: float,
    max_angle: float,
    base_oscillations: int,
    freq_step: float,
    spacing: float,
    arm_color: str,
    arm_width: float,
    bob_color_start: Color,
    bob_color_end: Color,
    quantize_freq: bool = False,
) -> list[VElement]:
    """Create pendulum VElements arranged in a horizontal row."""
    total_width = (count - 1) * spacing
    start_x = -total_width / 2

    specs = [
        PendulumSpec(
            pivot=Point2D(start_x + i * spacing, pivot_y),
            orientation=ORIENTATION_DOWN,
            freq=base_oscillations + i * freq_step,
        )
        for i in range(count)
    ]

    return create_pendulums(
        specs=specs,
        arm_length=arm_length,
        bob_radius=bob_radius,
        max_angle=max_angle,
        arm_color=arm_color,
        arm_width=arm_width,
        bob_color_start=bob_color_start,
        bob_color_end=bob_color_end,
        quantize_freq=quantize_freq,
    )
