"""Decorative circles and horizontal rule lines with animated entrance."""

import random
from dataclasses import replace

from svan2d.component.state import CircleState, LineState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement import VElement


def create_decoration_elements(
    scene_width: float,
    scene_height: float,
    decoration_start: float,
    decoration_end: float,
    style_cfg: dict,
    quote_bounds: tuple[float, float],
    rng: random.Random,
) -> list[VElement]:
    """Create decorative circles and horizontal lines.

    Args:
        quote_bounds: (min_y, max_y) of the quote text block.
    """
    elements: list[VElement] = []

    # --- Circles ---
    circle_count = style_cfg["circle_count"]
    circle_colors = [Color(c) for c in style_cfg["circle_colors"]]
    r_min, r_max = style_cfg["circle_radius_range"]
    q_min_y, q_max_y = quote_bounds

    circle_stagger = (decoration_end - decoration_start) * 0.6 / max(circle_count, 1)

    for i in range(circle_count):
        radius = rng.uniform(r_min, r_max)
        color = circle_colors[i % len(circle_colors)]

        # Position: scattered, avoiding central quote area
        margin = 40
        x = rng.uniform(-scene_width / 2 + margin, scene_width / 2 - margin)
        # Push circles above or below the quote block
        if rng.random() < 0.5:
            y = rng.uniform(-scene_height / 2 + margin, q_min_y - 10)
        else:
            y = rng.uniform(q_max_y + 10, scene_height / 2 - margin)

        visible = CircleState(
            radius=radius,
            fill_color=color,
            fill_opacity=0.4,
            pos=Point2D(x, y),
            scale=1.0,
            opacity=1.0,
        )
        hidden = replace(visible, scale=0.0, opacity=0.0)

        appear_at = decoration_start + i * circle_stagger
        appear_end = min(appear_at + (decoration_end - decoration_start) * 0.4, decoration_end)

        element = (
            VElement()
            .keystate(hidden, at=appear_at)
            .transition(easing_dict={
                "scale": easing.out_back,
                "opacity": easing.out_cubic,
            })
            .keystate(visible, at=appear_end)
            .keystate(visible, at=1.0)
        )
        elements.append(element)

    # --- Horizontal lines ---
    line_color = Color(style_cfg["line_color"])
    line_width = style_cfg["line_width"]
    line_length = scene_width * style_cfg["line_length_ratio"]

    # Line above quote block
    line_above_y = q_min_y - 15
    # Line between quote and author area
    line_below_y = q_max_y + 15

    for y_pos in [line_above_y, line_below_y]:
        visible = LineState(
            length=line_length,
            stroke_color=line_color,
            stroke_width=line_width,
            pos=Point2D(0, y_pos),
            scale=1.0,
            opacity=1.0,
        )
        hidden = replace(visible, scale=0.0, opacity=0.0)

        element = (
            VElement()
            .keystate(hidden, at=decoration_start)
            .transition(easing_dict={
                "scale": easing.out_cubic,
                "opacity": easing.out_cubic,
            })
            .keystate(visible, at=decoration_end)
            .keystate(visible, at=1.0)
        )
        elements.append(element)

    return elements
