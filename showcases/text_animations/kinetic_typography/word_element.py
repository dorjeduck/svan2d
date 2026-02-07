"""Per-character animated VElements with scatter, bezier curves, and varied easing."""

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
    units_per_em = font["head"].unitsPerEm
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


def create_word_char_elements(
    text: str,
    word_center: Point2D,
    color: Color,
    font_path: str,
    font_size: float,
    first_char_time: float,
    char_stagger: float,
    entrance_duration: float,
    exit_at: float,
    exit_duration: float,
    entrance: str,
    scatter_radius: float,
    scatter_rotation: float,
    rng: random.Random,
) -> list[VElement]:
    """Create one VElement per character in *text*, each with independent animation.

    Characters are positioned so the word is horizontally centred at *word_center*.
    """
    widths = measure_char_widths(font_path, text, font_size)
    total_width = sum(widths)

    # x positions: left-aligned then shifted so the block is centred
    x_positions: list[float] = []
    cursor = -total_width / 2
    for w in widths:
        # centre of this character cell
        x_positions.append(cursor + w / 2)
        cursor += w

    elements: list[VElement] = []
    for i, ch in enumerate(text):
        if ch == " ":
            continue

        target = Point2D(word_center.x + x_positions[i], word_center.y)
        appear_at = first_char_time + char_stagger * i

        element = _build_char_element(
            ch=ch,
            target=target,
            color=color,
            font_path=font_path,
            font_size=font_size,
            appear_at=appear_at,
            entrance_duration=entrance_duration,
            exit_at=exit_at + char_stagger * i,
            exit_duration=exit_duration,
            entrance=entrance,
            scatter_radius=scatter_radius,
            scatter_rotation=scatter_rotation,
            rng=rng,
        )
        elements.append(element)

    return elements


def _build_char_element(
    ch: str,
    target: Point2D,
    color: Color,
    font_path: str,
    font_size: float,
    appear_at: float,
    entrance_duration: float,
    exit_at: float,
    exit_duration: float,
    entrance: str,
    scatter_radius: float,
    scatter_rotation: float,
    rng: random.Random,
) -> VElement:
    """Build a single character's VElement with entrance → hold → exit."""

    visible = TextPathState(
        text=ch,
        font_path=font_path,
        font_size=font_size,
        fill_color=color,
        pos=target,
        scale=1.0,
        opacity=1.0,
        rotation=0.0,
    )

    hidden, enter_easing, enter_curve = _entrance_state(
        visible, target, entrance, scatter_radius, scatter_rotation, rng
    )

    appear_end = min(appear_at + entrance_duration, 1.0)
    exit_end = min(exit_at + exit_duration, 1.0)

    # Reverse curve: mirror the bezier control point for exit
    exit_hidden, exit_curve = _exit_state(hidden, enter_curve, target, rng)

    builder = VElement().keystate(hidden, at=appear_at)

    # Entrance transition — curve + easing
    trans_kwargs: dict = {"easing_dict": enter_easing}
    if enter_curve:
        trans_kwargs["curve_dict"] = enter_curve
    builder = builder.transition(**trans_kwargs)

    builder = builder.keystate(visible, at=appear_end)

    # Hold
    builder = builder.keystate(visible, at=exit_at)

    # Exit transition
    exit_trans: dict = {"easing_dict": enter_easing}
    if exit_curve:
        exit_trans["curve_dict"] = exit_curve
    builder = builder.transition(**exit_trans)

    builder = builder.keystate(exit_hidden, at=exit_end)

    return builder


# ---------------------------------------------------------------------------
# Entrance strategies
# ---------------------------------------------------------------------------

def _entrance_state(
    visible: TextPathState,
    target: Point2D,
    entrance: str,
    scatter_radius: float,
    scatter_rotation: float,
    rng: random.Random,
) -> tuple[TextPathState, dict, dict | None]:
    """Return (hidden_state, easing_dict, curve_dict | None)."""

    if entrance == "scatter":
        return _entrance_scatter(visible, target, scatter_radius, scatter_rotation, rng)
    elif entrance == "rain":
        return _entrance_rain(visible, target, scatter_radius, rng)
    elif entrance == "explode":
        return _entrance_explode(visible, target, scatter_radius, scatter_rotation, rng)
    elif entrance == "spiral":
        return _entrance_spiral(visible, target, scatter_radius, scatter_rotation, rng)
    else:
        raise ValueError(f"Unknown entrance '{entrance}'")


def _entrance_scatter(visible, target, radius, max_rot, rng):
    """Characters fly in from random positions along bezier arcs."""
    angle = rng.uniform(0, 2 * math.pi)
    dist = rng.uniform(radius * 0.6, radius)
    origin = Point2D(target.x + math.cos(angle) * dist,
                     target.y + math.sin(angle) * dist)
    rot = rng.uniform(-max_rot, max_rot)

    hidden = replace(visible, pos=origin, scale=0.0, opacity=0.0, rotation=rot)

    # Bezier control point: perpendicular to the line origin→target
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

    return hidden, easing_dict, curve_dict


def _entrance_rain(visible, target, radius, rng):
    """Characters drop in from above with slight horizontal drift."""
    x_drift = rng.uniform(-60, 60)
    origin = Point2D(target.x + x_drift, target.y - radius)

    hidden = replace(visible, pos=origin, opacity=0.0, scale=0.6)

    easing_dict = {
        "pos": easing2D(easing.out_cubic, easing.out_bounce),
        "opacity": easing.out_cubic,
        "scale": easing.out_back,
    }
    return hidden, easing_dict, None


def _entrance_explode(visible, _target, _radius, max_rot, rng):
    """Characters burst outward from the centre then converge (reversed)."""
    rot = rng.uniform(-max_rot, max_rot)
    hidden = replace(visible, pos=Point2D(0, 0), scale=0.0, opacity=0.0, rotation=rot)

    easing_dict = {
        "pos": easing.out_expo,
        "scale": easing.out_back,
        "opacity": easing.out_cubic,
        "rotation": easing.out_cubic,
    }
    return hidden, easing_dict, None


def _entrance_spiral(visible, target, radius, max_rot, rng):
    """Characters spiral in from a wide circular orbit with a pronounced arc."""
    # Consistent base angle with small per-character jitter for a cohesive swirl
    base_angle = rng.uniform(0, 2 * math.pi)
    angle = base_angle + rng.uniform(-0.3, 0.3)
    dist = rng.uniform(radius * 0.9, radius * 1.2)
    origin = Point2D(target.x + math.cos(angle) * dist,
                     target.y + math.sin(angle) * dist)

    # Consistent positive rotation for unified spin direction
    rot = rng.uniform(max_rot * 0.6, max_rot)

    hidden = replace(visible, pos=origin, scale=0.0, opacity=0.0, rotation=rot)

    # Wide arc for a pronounced spiral trajectory
    arc_radius = dist * 1.8
    curve_dict = {"pos": curve.arc_clockwise(arc_radius)}

    easing_dict = {
        "pos": easing2D(easing.out_cubic, easing.out_back),
        "scale": easing.out_back,
        "opacity": easing.out_cubic,
        "rotation": easing.out_cubic,
    }
    return hidden, easing_dict, curve_dict


# ---------------------------------------------------------------------------
# Exit helper
# ---------------------------------------------------------------------------

def _exit_state(hidden, enter_curve, _target, _rng):
    """Build exit hidden state and curve (mirror of entrance)."""
    return hidden, enter_curve
