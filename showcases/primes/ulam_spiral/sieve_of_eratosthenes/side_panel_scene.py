from dataclasses import replace

from svan2d.component.state.square import SquareState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement.velement import VElement
from svan2d.vscene.vscene import VScene

from config import (
    COLOR_COMPOSITE,
    COLOR_CURRENT_SIEVE_PRIME,
    COLOR_ONE,
    COLOR_PRIME,
    COLOR_BACKGROUND,
    COLOR_CANDIDATE,
)


def create_side_panel(
    panel_width: int,
    panel_height: int,
    step_stats: list,
    scale_factor: float = 1.0,
):
    """
    Create the side panel with step counter and statistics.

    step_stats: list of dicts with keys: sieve_prime, num_primes, num_composites, num_unclassified
    scale_factor: multiplier for text sizes to maintain consistent appearance across different scene sizes
    """
    num_steps = len(step_stats) - 1  # steps are 0 to num_steps
    text_size = 80 * scale_factor
    label_size = 80 * scale_factor

    pos_x = -panel_width / 2 + text_size

    scene = VScene(
        width=panel_width,
        height=panel_height,
        background=COLOR_BACKGROUND,
    )

    pos_y = -panel_height / 2 + 80 * scale_factor + text_size
    step_time = 1 / num_steps

    # All stats including step counter use TextState with discrete jumps
    stats_config = [
        ("Step:", "step", Color(255, 255, 255)),
        ("Current Sieve Prime:", "sieve_prime", COLOR_CURRENT_SIEVE_PRIME),
        ("Number of Primes:", "num_primes", COLOR_PRIME),
        ("Number of Composites:", "num_composites", Color(255, 255, 255)),
        ("Unclassified:", "num_unclassified", Color(255, 255, 255)),
    ]

    for label_text, stat_key, color in stats_config:
        # Label
        label_state = TextState(
            text=label_text,
            pos=Point2D(pos_x, pos_y),
            font_size=label_size,
            fill_color=color,
            text_anchor="left",
        )
        label_element = VElement().keystates([label_state, label_state])
        scene = scene.add_element(label_element)

        pos_y = pos_y + 1.4 * label_size

        # Value display with dual-state keystates for discrete jumps
        base_text_state = TextState(
            text="",
            pos=Point2D(pos_x, pos_y),
            font_size=text_size,
            fill_color=color,
            text_anchor="left",
        )

        counter_element = VElement()

        for step in range(num_steps + 1):
            # "step" uses the step number directly, others read from step_stats
            if stat_key == "step":
                value = step
                next_value = step + 1 if step < num_steps else step
            else:
                value = step_stats[step][stat_key]
                next_value = (
                    step_stats[step + 1][stat_key] if step < num_steps else value
                )

            text = "-" if value is None else str(value)
            t = step * step_time
            state = replace(base_text_state, text=text)

            if step == num_steps:
                counter_element = counter_element.keystate([state, state], at=1.0)
            else:
                next_text = "-" if next_value is None else str(next_value)
                next_state = replace(base_text_state, text=next_text)
                counter_element = counter_element.keystate([state, next_state], at=t)

        scene = scene.add_element(counter_element)
        pos_y = pos_y + 2 * text_size

    # legend

    legend_text_size = 80 * scale_factor

    vert_dist = legend_text_size + 30 * scale_factor
    start_y = panel_height / 2 - 7 * legend_text_size

    colors = [
        COLOR_ONE,
        COLOR_COMPOSITE,
        COLOR_PRIME,
        COLOR_CURRENT_SIEVE_PRIME,
        COLOR_CANDIDATE,
    ]

    square_states = [
        SquareState(
            size=legend_text_size,
            pos=Point2D(
                -panel_width / 2 + 1.5 * legend_text_size, start_y + i * vert_dist
            ),
            fill_color=color,
            stroke_color=Color(255, 255, 255),
            stroke_width=2,
        )
        for i, color in enumerate(colors)
    ]

    square_elements = [VElement().keystates([state, state]) for state in square_states]

    scene = scene.add_elements(square_elements)

    texts = ["Number 1", "Composite", "Prime", "Current Sieve Prime", "Unclassified"]

    text_states = [
        TextState(
            text=text,
            pos=Point2D(
                -panel_width / 2 + 2.5 * legend_text_size, start_y + i * vert_dist
            ),
            font_size=legend_text_size,
            fill_color=Color(255, 255, 255),
            text_anchor="left",
        )
        for i, text in enumerate(texts)
    ]

    text_elements = [VElement().keystates([state, state]) for state in text_states]

    return scene.add_elements(text_elements)
