"""Element construction for the grid pendulum waves showcase."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from pendulum import PendulumSpec, create_pendulums

from svan2d import Color, Point2D, VElement

ORIENTATION_DOWN = -math.pi / 2


def create_pendulum_elements(
    rows: int,
    cols: int,
    pivot_y: float,
    arm_length: float,
    bob_radius: float,
    max_angle: float,
    base_oscillations: int,
    freq_step_col: float,
    freq_step_row: float,
    spacing: float,
    arm_color: str,
    arm_width: float,
    bob_color_start: Color,
    bob_color_end: Color,
    quantize_freq: bool = False,
) -> list[VElement]:
    """Create pendulum VElements arranged in a grid.

    Frequency increases by column (freq_step_col) and by row (freq_step_row),
    creating 2D wave interference patterns.
    """
    total_w = (cols - 1) * spacing
    total_h = (rows - 1) * spacing
    start_x = -total_w / 2
    start_y_offset = -total_h / 2

    specs = [
        PendulumSpec(
            pivot=Point2D(
                start_x + col * spacing,
                pivot_y + start_y_offset + row * spacing,
            ),
            orientation=ORIENTATION_DOWN,
            freq=base_oscillations + col * freq_step_col + row * freq_step_row,
        )
        for row in range(rows)
        for col in range(cols)
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
