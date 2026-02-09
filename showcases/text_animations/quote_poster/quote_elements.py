"""Per-character quote VElements with scatter entrance animation."""

import math
import random
from dataclasses import replace

from svan2d.component.state import TextPathState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.font.glyph_cache import get_glyph_cache
from svan2d.font.glyph_extractor import load_font
from svan2d.transition import curve, easing
from svan2d.transition.easing import easing2D
from svan2d.velement import VElement


def measure_char_widths(font_path: str, text: str, font_size: float) -> list[float]:
    """Get pixel-space advance width for each character using the glyph cache."""
    cache = get_glyph_cache()
    font = load_font(font_path)
    units_per_em = font["head"].unitsPerEm # type: ignore
    scale = font_size / units_per_em

    widths = []
    for ch in text:
        if ch == " ":
            try:
                g = cache.get_glyph(font_path, "n", font=font)
                widths.append(g.advance_width * scale)
            except ValueError:
                widths.append(font_size * 0.3)
        else:
            try:
                g = cache.get_glyph(font_path, ch, font=font)
                widths.append(g.advance_width * scale)
            except ValueError:
                widths.append(font_size * 0.5)
    return widths


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
    # Offset upward to leave room for author below
    start_y = -total_text_height / 2 - font_size * 0.5

    # Count total visible chars for stagger calculation
    total_visible_chars = sum(len(ch) for line in lines for ch in line if ch != " ")
    if total_visible_chars == 0:
        return []

    entrance_window = entrance_end - entrance_start
    char_stagger = entrance_window / total_visible_chars
    entrance_dur = entrance_window * 0.3

    elements: list[VElement] = []
    global_char_idx = 0

    for line_idx, line in enumerate(lines):
        widths = measure_char_widths(font_path, line, font_size)
        total_width = sum(widths)

        # Centre each line horizontally
        x_positions: list[float] = []
        cursor = -total_width / 2
        for w in widths:
            x_positions.append(cursor + w / 2)
            cursor += w

        y = start_y + line_idx * line_height

        for i, ch in enumerate(line):
            if ch == " ":
                continue

            target = Point2D(x_positions[i], y)
            appear_time = entrance_start + global_char_idx * char_stagger
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

            # Scatter entrance: random origin
            angle = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(scatter_radius * 0.6, scatter_radius)
            origin = Point2D(
                target.x + math.cos(angle) * dist,
                target.y + math.sin(angle) * dist,
            )
            rot = rng.uniform(-scatter_rotation, scatter_rotation)

            hidden = replace(visible, pos=origin, scale=0.0, opacity=0.0, rotation=rot)

            # Bezier control point: perpendicular to origin→target
            mid = Point2D((origin.x + target.x) / 2, (origin.y + target.y) / 2)
            dx, dy = target.x - origin.x, target.y - origin.y
            perp_scale = rng.uniform(-0.4, 0.4)
            cp = Point2D(mid.x + (-dy) * perp_scale, mid.y + dx * perp_scale)

            easing_dict = {
                "pos": easing2D(easing.out_cubic, easing.out_back),
                "scale": easing.out_back,
                "opacity": easing.out_cubic,
                "rotation": easing.out_cubic,
            }
            curve_dict = {"pos": curve.bezier([cp])}

            element = (
                VElement()
                .keystate(hidden, at=appear_time)
                .transition(easing_dict=easing_dict, curve_dict=curve_dict)
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
    start_y = -total_text_height / 2 - font_size * 0.5
    min_y = start_y - font_size * 0.5
    max_y = start_y + (len(lines) - 1) * line_height + font_size * 0.5
    return min_y, max_y
