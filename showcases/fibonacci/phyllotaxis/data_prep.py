"""Data preparation for the phyllotaxis showcase.

Two-phase animation:
  Phase 1 — seeds appear one by one in neutral color
  Phase 2 — spiral families light up with color
"""

import math
from dataclasses import dataclass

from phyllotaxis import seed_position, spiral_family, fibonacci
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D


@dataclass
class SeedData:
    index: int
    pos: Point2D
    appear_time: float
    family: int
    color: Color
    neutral_color: Color
    radius: float


@dataclass
class PhyllotaxisData:
    seeds: list[SeedData]
    family_reveal_times: list[float]
    appear_end: float
    anim_end: float


def prepare(cfg: dict) -> PhyllotaxisData:
    num_families = fibonacci(cfg["phyllotaxis"]["spiral_fib_index"])
    seeds_per_arm = cfg["phyllotaxis"]["seeds_per_arm"]
    num_seeds = num_families * seeds_per_arm
    c = cfg["phyllotaxis"]["spacing_constant"]
    appear_ratio = cfg["animation"]["appear_ratio"]
    reveal_ratio = cfg["animation"]["reveal_ratio"]
    color_1 = Color(cfg["style"]["color_1"])
    color_2 = Color(cfg["style"]["color_2"])
    neutral = Color(cfg["style"]["neutral_color"])
    seed_radius = cfg["style"]["seed_radius"]

    appear_end = appear_ratio
    anim_end = appear_ratio + reveal_ratio

    seeds = []
    for i in range(num_seeds):
        x, y = seed_position(i, c)
        fam = spiral_family(i, num_families)
        color = color_1.interpolate(color_2, fam / max(num_families - 1, 1))
        appear_time = math.sqrt(i / num_seeds) * appear_end

        seeds.append(
            SeedData(
                index=i,
                pos=Point2D(x, y),
                appear_time=appear_time,
                family=fam,
                color=color,
                neutral_color=neutral,
                radius=seed_radius,
            )
        )

    family_reveal_times = [
        appear_end + (f / num_families) * reveal_ratio
        for f in range(num_families)
    ]

    return PhyllotaxisData(
        seeds=seeds,
        family_reveal_times=family_reveal_times,
        appear_end=appear_end,
        anim_end=anim_end,
    )
