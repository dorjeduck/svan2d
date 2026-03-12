"""Element construction for the double ring pendulum waves showcase."""

import math
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from pendulum import PendulumSpec, create_pendulums

from svan2d import Color, Point2D, VElement


@dataclass
class RingConfig:
    """Per-ring configuration."""

    count: int
    radius: float
    arm_length: float
    bob_radius: float
    max_angle: float
    base_oscillations: int
    freq_step: float
    arm_color: str
    arm_width: float
    bob_color_start: Color
    bob_color_end: Color
    start_angle: float = 180.0
    clockwise: bool = True


def _build_ring_specs(ring: RingConfig, angle_offset: float = 0.0) -> list[PendulumSpec]:
    """Build PendulumSpecs for a single ring."""
    start_rad = math.radians(ring.start_angle - 90)
    direction = 1 if ring.clockwise else -1
    specs = []
    for i in range(ring.count):
        angle = direction * 2 * math.pi * i / ring.count + start_rad + angle_offset
        specs.append(
            PendulumSpec(
                pivot=Point2D(
                    ring.radius * math.cos(angle),
                    ring.radius * math.sin(angle),
                ),
                orientation=angle,
                freq=ring.base_oscillations + i * ring.freq_step,
            )
        )
    return specs


def create_pendulum_elements(
    inner: RingConfig,
    outer: RingConfig,
    quantize_freq: bool = False,
) -> list[VElement]:
    """Create pendulum VElements on two concentric rings, hanging radially outward."""
    inner_specs = _build_ring_specs(inner)
    outer_specs = _build_ring_specs(outer, angle_offset=math.pi / outer.count)

    inner_elements = create_pendulums(
        specs=inner_specs,
        arm_length=inner.arm_length,
        bob_radius=inner.bob_radius,
        max_angle=inner.max_angle,
        arm_color=inner.arm_color,
        arm_width=inner.arm_width,
        bob_color_start=inner.bob_color_start,
        bob_color_end=inner.bob_color_end,
        quantize_freq=quantize_freq,
    )

    outer_elements = create_pendulums(
        specs=outer_specs,
        arm_length=outer.arm_length,
        bob_radius=outer.bob_radius,
        max_angle=outer.max_angle,
        arm_color=outer.arm_color,
        arm_width=outer.arm_width,
        bob_color_start=outer.bob_color_start,
        bob_color_end=outer.bob_color_end,
        quantize_freq=quantize_freq,
    )

    return inner_elements + outer_elements
