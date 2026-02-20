"""Seed elements for the phyllotaxis showcase.

Seeds appear one by one in neutral gray, then spiral families
light up with color revealing the Fibonacci structure.
"""

import math

from data_prep import SeedData, PhyllotaxisData
from svan2d.component.state.circle import CircleState
from svan2d.transition import easing
from svan2d.velement.velement import VElement


def create_seed_elements(data: PhyllotaxisData, style_cfg: dict) -> list[VElement]:
    """Create VElements: hidden → neutral → colored."""
    target_opacity = style_cfg["opacity"]
    fade_duration = 0.006

    num_families = len(data.family_reveal_times)
    reveal_dur = (data.anim_end - data.appear_end) / max(num_families, 1) * 0.5

    # Count seeds per family for stagger calculation
    family_counts: dict[int, int] = {}
    for seed in data.seeds:
        family_counts[seed.family] = family_counts.get(seed.family, 0) + 1

    # Track position within family (center→outward)
    family_counters: dict[int, int] = {}

    elements = []

    for seed in data.seeds:
        t_in = seed.appear_time
        t_visible = min(t_in + fade_duration, data.appear_end)

        hidden = CircleState(
            radius=0.1,
            pos=seed.pos,
            fill_color=seed.neutral_color,
            opacity=0.0,
        )
        neutral = CircleState(
            radius=seed.radius,
            pos=seed.pos,
            fill_color=seed.neutral_color,
            opacity=target_opacity * 0.5,
        )

        el = VElement().keystate(hidden, at=t_in)
        el = el.transition(easing_dict={"opacity": easing.out_quad})
        el = el.keystate(neutral, at=t_visible)

        # Color reveal — staggered from center outward within family
        pos_in_family = family_counters.get(seed.family, 0)
        family_counters[seed.family] = pos_in_family + 1
        count = family_counts[seed.family]
        stagger = (pos_in_family / max(count - 1, 1)) * reveal_dur * 0.8

        t_reveal = data.family_reveal_times[seed.family] + stagger
        t_colored = min(t_reveal + fade_duration, data.anim_end)

        colored = CircleState(
            radius=seed.radius * 1.1,
            pos=seed.pos,
            fill_color=seed.color,
            opacity=target_opacity,
        )

        if t_visible < t_reveal:
            el = el.keystate(neutral, at=t_reveal)
        el = el.transition(easing_dict={"opacity": easing.out_quad})
        el = el.keystate(colored, at=t_colored)

        if t_colored < 1.0:
            el = el.keystate(colored, at=1.0)

        elements.append(el)

    return elements


def compute_max_extent(seeds: list[SeedData]) -> float:
    if not seeds:
        return 1.0
    return max(math.sqrt(s.pos.x ** 2 + s.pos.y ** 2) + s.radius for s in seeds)
