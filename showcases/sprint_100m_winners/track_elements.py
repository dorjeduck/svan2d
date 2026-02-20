"""Track elements for Olympic 100m Winners Race.

Creates lane backgrounds, distance markers, finish line, race title,
and animated clock display for a single 10-lane scene.
Fading elements use keystates to fade out during results transition.
"""

from dataclasses import replace

from svan2d.component.state.line import LineState
from svan2d.component.state.number import NumberFormat, NumberState
from svan2d.component.state.rectangle import RectangleState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement.velement import VElement


def _static(state) -> VElement:
    """Create a static VElement from a single state."""
    return VElement().keystates(states=[state, state])


def _fading(state, timing: dict) -> VElement:
    """Create a VElement that fades out during results transition."""
    faded = replace(state, opacity=0.0)
    return (
        VElement()
        .keystate(state, at=0.0)
        .keystate(state, at=timing["results_start"])
        .keystate(faded, at=timing["results_end"])
        .keystate(faded, at=1.0)
    )


def _track_layout(cfg: dict) -> dict:
    """Calculate track area bounds from config (center origin)."""
    w = cfg["scene"]["width"]
    h = cfg["scene"]["height"]
    tc = cfg["track"]

    track_left = -w / 2 + tc["margin_left"]
    track_right = w / 2 - tc["margin_right"]
    track_top = -h / 2 + tc["margin_top"]
    track_bottom = h / 2 - tc["margin_bottom"]

    return {
        "track_left": track_left,
        "track_right": track_right,
        "track_top": track_top,
        "track_bottom": track_bottom,
        "track_width": track_right - track_left,
        "track_height": track_bottom - track_top,
    }


def distance_to_x(distance: float, layout: dict) -> float:
    """Map distance (0–100m) to X coordinate."""
    t = distance / 100.0
    return layout["track_left"] + t * layout["track_width"]


def create_lane_backgrounds(
    num_lanes: int,
    layout: dict,
    timing: dict,
    cfg: dict,
) -> list[VElement]:
    """Create alternating lane background rectangles that fade during results."""
    elements = []
    tc = cfg["track"]
    lane_h = tc["lane_height"]
    lane_gap = tc["lane_gap"]
    colors = tc["lane_colors"]

    for i in range(num_lanes):
        y = layout["track_top"] + i * (lane_h + lane_gap) + lane_h / 2
        color_idx = i % len(colors)

        state = RectangleState(
            pos=Point2D(
                layout["track_left"] + layout["track_width"] / 2,
                y,
            ),
            width=layout["track_width"],
            height=lane_h,
            fill_color=Color(colors[color_idx]),
            fill_opacity=0.6,
            stroke_color=Color.NONE,
            z_index=-10.0,
        )
        elements.append(_fading(state, timing))

    return elements


def create_distance_markers(
    num_lanes: int,
    layout: dict,
    timing: dict,
    cfg: dict,
) -> list[VElement]:
    """Create vertical distance marker lines and labels that fade during results."""
    elements = []
    tc = cfg["track"]
    distances = tc["marker_distances"]
    lane_h = tc["lane_height"]
    lane_gap = tc["lane_gap"]

    lanes_height = num_lanes * lane_h + (num_lanes - 1) * lane_gap
    lanes_center_y = layout["track_top"] + lanes_height / 2

    for dist in distances:
        x = distance_to_x(dist, layout)

        line_state = LineState(
            pos=Point2D(x, lanes_center_y),
            length=lanes_height,
            rotation=90,
            stroke_color=Color(tc["marker_color"]),
            stroke_width=tc["marker_width"],
            stroke_opacity=0.4,
            z_index=-8.0,
        )
        elements.append(_fading(line_state, timing))

        label_y = layout["track_top"] + lanes_height + 6
        label_state = TextState(
            text=f"{dist}m",
            pos=Point2D(x, label_y),
            font_family=tc["marker_font_family"],
            font_size=tc["marker_font_size"],
            fill_color=Color(tc["marker_label_color"]),
            text_anchor="middle",
            dominant_baseline="hanging",
            z_index=-5.0,
        )
        elements.append(_fading(label_state, timing))

    return elements


def create_finish_line(
    num_lanes: int,
    layout: dict,
    timing: dict,
    cfg: dict,
) -> VElement:
    """Create the finish line at 100m that fades during results."""
    tc = cfg["track"]
    lane_h = tc["lane_height"]
    lane_gap = tc["lane_gap"]
    x = distance_to_x(100.0, layout)

    lanes_height = num_lanes * lane_h + (num_lanes - 1) * lane_gap
    lanes_center_y = layout["track_top"] + lanes_height / 2

    state = LineState(
        pos=Point2D(x, lanes_center_y),
        length=lanes_height,
        rotation=90,
        stroke_color=Color(tc["finish_color"]),
        stroke_width=tc["finish_width"],
        stroke_opacity=tc["finish_opacity"],
        stroke_dasharray="4,3",
        z_index=-2.0,
    )
    return _fading(state, timing)


def create_title(layout: dict, cfg: dict) -> VElement:
    """Create the race title text above track area, left-aligned."""
    tc = cfg["title"]
    y = layout["track_top"] - tc["padding_above"]

    return _static(TextState(
        text="Olympic 100m Winners 1988\u20132024",
        pos=Point2D(layout["track_left"], y),
        font_family=tc["font_family"],
        font_size=tc["font_size"],
        font_weight=tc["font_weight"],
        fill_color=Color(tc["color"]),
        text_anchor="start",
        dominant_baseline="auto",
        z_index=5.0,
    ))


def create_clock_element(
    max_time: float,
    timing: dict,
    layout: dict,
    cfg: dict,
) -> VElement:
    """Create animated clock above track area using NumberState."""
    cc = cfg["clock"]
    race_start = timing["race_start"]
    total_duration = timing["total_duration"]
    race_finish_at = race_start + max_time / total_duration
    y = layout["track_top"] - cc["padding_above"]

    clock_base = dict(
        pos=Point2D(layout["track_right"], y),
        suffix="s",
        format=NumberFormat.FIXED,
        decimals=2,
        font_family=cc["font_family"],
        font_size=cc["font_size"],
        font_weight=cc["font_weight"],
        fill_color=Color(cc["color"]),
        text_anchor="end",
        dominant_baseline="auto",
        z_index=10.0,
    )

    return (
        VElement()
        .keystate(NumberState(value=0.0, fill_opacity=0.0, **clock_base), at=0.0)
        .keystate(
            [
                NumberState(value=0.0, fill_opacity=0.0, **clock_base),
                NumberState(value=0.0, **clock_base),
            ],
            at=race_start,
        )
        .keystate(
            [
                NumberState(value=max_time, **clock_base),
                NumberState(value=max_time, fill_opacity=0.0, **clock_base),
            ],
            at=race_finish_at,
        )
        .keystate(NumberState(value=max_time, fill_opacity=0.0, **clock_base), at=1.0)
    )


def create_track_elements(
    num_lanes: int,
    max_time: float,
    timing: dict,
    cfg: dict,
) -> list[VElement]:
    """Create all track elements for the single race scene."""
    layout = _track_layout(cfg)

    elements = []
    elements.extend(create_lane_backgrounds(num_lanes, layout, timing, cfg))
    elements.extend(create_distance_markers(num_lanes, layout, timing, cfg))
    elements.append(create_finish_line(num_lanes, layout, timing, cfg))
    elements.append(create_title(layout, cfg))
    elements.append(create_clock_element(max_time, timing, layout, cfg))

    return elements
