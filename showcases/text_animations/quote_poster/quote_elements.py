"""Per-character quote VElements with scatter entrance animation."""

import random
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from scatter_entrance import scatter_entrance

from svan2d.component.state import TextPathState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.font import get_font_glyphs
from svan2d.utils.stagger_schedule import StaggerSchedule
from svan2d.velement import VElement


def create_quote_elements(
    lines: list[str],
    font_path: str,
    font_size: float,
    quote_color: Color,
    scatter_radius: float,
    scatter_rotation: float,
    entrance_start: float,
    entrance_end: float,
    rng: random.Random,
) -> list[VElement]:
    """Create per-character VElements for the quote with scatter entrance."""
    line_height = font_size * 1.4
    total_text_height = (len(lines) - 1) * line_height
    # Offset upward to leave room for author below (Cartesian: top = positive y)
    start_y = total_text_height / 2 + font_size * 0.5

    # Count total visible chars for stagger calculation
    total_visible_chars = sum(len(ch) for line in lines for ch in line if ch != " ")
    if total_visible_chars == 0:
        return []

    entrance_window = entrance_end - entrance_start
    entrance_dur = entrance_window * 0.3
    schedule = StaggerSchedule(total_visible_chars, t_start=entrance_start, t_end=entrance_end, overlap=0.0)

    font = get_font_glyphs(font_path)
    elements: list[VElement] = []
    global_char_idx = 0

    for line_idx, line in enumerate(lines):
        x_positions = font.centered_char_x_positions(line, font_size)

        y = start_y - line_idx * line_height

        for i, ch in enumerate(line):
            if ch == " ":
                continue

            target = Point2D(x_positions[i], y)
            appear_time = schedule[global_char_idx][0]
            appear_end = min(appear_time + entrance_dur, entrance_end)

            visible = TextPathState(
                text=ch,
                font_path=font_path,
                font_size=font_size,
                fill_color=quote_color,
                pos=target,
                scale=1.0,
                opacity=1.0,
                rotation=0.0,
                text_anchor="middle",
            )

            origin, rot, easing_dict, interpolation_dict = scatter_entrance(
                target, scatter_radius, scatter_rotation, rng
            )
            hidden = replace(visible, pos=origin, scale=0.0, opacity=0.0, rotation=rot)

            element = (
                VElement()
                .keystate(hidden, at=appear_time)
                .transition(
                    easing_dict=easing_dict, interpolation_dict=interpolation_dict
                )
                .keystate(visible, at=appear_end)
                .keystate(visible, at=1.0)
            )
            elements.append(element)
            global_char_idx += 1

    return elements


def get_quote_block_bounds(
    lines: list[str],
    font_size: float,
) -> tuple[float, float]:
    """Return (min_y, max_y) of the quote text block, matching create_quote_elements layout."""
    line_height = font_size * 1.4
    total_text_height = (len(lines) - 1) * line_height
    start_y = total_text_height / 2 + font_size * 0.5
    max_y = start_y + font_size * 0.5
    min_y = start_y - (len(lines) - 1) * line_height - font_size * 0.5
    return min_y, max_y
