"""Element construction for the ring pendulum waves showcase."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from pendulum import PendulumSpec, create_pendulums

from svan2d import Color, Point2D, VElement


def create_pendulum_elements(
    count: int,
    circle_radius: float,
    arm_length: float,
    bob_radius: float,
    max_angle: float,
    base_oscillations: int,
    freq_step: float,
    arm_color: str,
    arm_width: float,
    bob_color_start: Color,
    bob_color_end: Color,
    quantize_freq: bool = False,
    start_angle: float = 180.0,
    clockwise: bool = True,
) -> list[VElement]:
    """Create pendulum VElements arranged in a ring, hanging radially outward."""
    start_rad = math.radians(90 - start_angle)
    direction = -1 if clockwise else 1
    specs = []
    for i in range(count):
        angle = direction * 2 * math.pi * i / count + start_rad
        specs.append(
            PendulumSpec(
                pivot=Point2D(
                    circle_radius * math.cos(angle),
                    circle_radius * math.sin(angle),
                ),
                orientation=angle,
                freq=base_oscillations + i * freq_step,
            )
        )

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
