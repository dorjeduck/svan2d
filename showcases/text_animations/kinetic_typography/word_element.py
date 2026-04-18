"""Per-character animated VElements with scatter, bezier curves, and varied easing."""

import math
import random
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from scatter_entrance import scatter_entrance as _scatter_entrance

from svan2d.primitive.state import TextPathState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.font import get_font_glyphs
from svan2d.transition import curve, easing
from svan2d.transition.easing import easing2D
from svan2d.utils.stagger_schedule import StaggerSchedule
from svan2d.velement import VElement


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
    x_positions = get_font_glyphs(font_path).centered_char_x_positions(text, font_size)

    n = len(text)
    entrance_sched = StaggerSchedule(n, t_start=first_char_time, t_end=first_char_time + n * char_stagger, overlap=0.0)
    exit_sched = StaggerSchedule(n, t_start=exit_at, t_end=exit_at + n * char_stagger, overlap=0.0)

    elements: list[VElement] = []
    for i, ch in enumerate(text):
        if ch == " ":
            continue

        target = Point2D(word_center.x + x_positions[i], word_center.y)

        element = _build_char_element(
            ch=ch,
            target=target,
            color=color,
            font_path=font_path,
            font_size=font_size,
            appear_at=entrance_sched[i][0],
            entrance_duration=entrance_duration,
            exit_at=exit_sched[i][0],
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
        trans_kwargs["interpolation_dict"] = enter_curve
    builder = builder.transition(**trans_kwargs)

    builder = builder.keystate(visible, at=appear_end)

    # Hold
    builder = builder.keystate(visible, at=exit_at)

    # Exit transition
    exit_trans: dict = {"easing_dict": enter_easing}
    if exit_curve:
        exit_trans["interpolation_dict"] = exit_curve
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
    """Return (hidden_state, easing_dict, interpolation_dict | None)."""

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
    origin, rot, easing_dict, interpolation_dict = _scatter_entrance(target, radius, max_rot, rng)
    hidden = replace(visible, pos=origin, scale=0.0, opacity=0.0, rotation=rot)
    return hidden, easing_dict, interpolation_dict


def _entrance_rain(visible, target, radius, rng):
    """Characters drop in from above with slight horizontal drift."""
    x_drift = rng.uniform(-60, 60)
    origin = Point2D(target.x + x_drift, target.y + radius)

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
    origin = Point2D(
        target.x + math.cos(angle) * dist, target.y + math.sin(angle) * dist
    )

    # Consistent positive rotation for unified spin direction
    rot = rng.uniform(max_rot * 0.6, max_rot)

    hidden = replace(visible, pos=origin, scale=0.0, opacity=0.0, rotation=rot)

    # Wide arc for a pronounced spiral trajectory
    arc_radius = dist * 1.8
    interpolation_dict = {"pos": curve.arc_clockwise(arc_radius)}

    easing_dict = {
        "pos": easing2D(easing.out_cubic, easing.out_back),
        "scale": easing.out_back,
        "opacity": easing.out_cubic,
        "rotation": easing.out_cubic,
    }
    return hidden, easing_dict, interpolation_dict


# ---------------------------------------------------------------------------
# Exit helper
# ---------------------------------------------------------------------------


def _exit_state(hidden, enter_curve, _target, _rng):
    """Build exit hidden state and curve (mirror of entrance)."""
    return hidden, enter_curve
