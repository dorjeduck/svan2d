"""Static track elements for 100m Sprint Race Replay.

Creates lane backgrounds, distance markers, finish line, race title,
and animated clock display.
"""

from svan2d.component.state.line import LineState
from svan2d.component.state.number import NumberFormat, NumberState
from svan2d.component.state.rectangle import RectangleState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement.velement import VElement

from data_prep import RaceData


def _static(state) -> VElement:
    """Create a static VElement from a single state."""
    return VElement().keystates(states=[state, state])


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
    cfg: dict,
) -> list[VElement]:
    """Create alternating lane background rectangles."""
    elements = []
    tc = cfg["track"]
    lane_h = tc["lane_height"]
    lane_gap = tc["lane_gap"]
    colors = tc["lane_colors"]

    for i in range(num_lanes):
        y = layout["track_top"] + i * (lane_h + lane_gap) + lane_h / 2
        color_idx = i % len(colors)

        elements.append(_static(RectangleState(
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
        )))

    return elements


def create_distance_markers(
    num_lanes: int,
    layout: dict,
    cfg: dict,
) -> list[VElement]:
    """Create vertical distance marker lines and labels spanning lanes only."""
    elements = []
    tc = cfg["track"]
    distances = tc["marker_distances"]
    lane_h = tc["lane_height"]
    lane_gap = tc["lane_gap"]

    # Span markers across actual lane area, not full track height
    lanes_height = num_lanes * lane_h + (num_lanes - 1) * lane_gap
    lanes_center_y = layout["track_top"] + lanes_height / 2

    for dist in distances:
        x = distance_to_x(dist, layout)

        # Vertical marker line
        elements.append(_static(LineState(
            pos=Point2D(x, lanes_center_y),
            length=lanes_height,
            rotation=90,
            stroke_color=Color(tc["marker_color"]),
            stroke_width=tc["marker_width"],
            stroke_opacity=0.4,
            z_index=-8.0,
        )))

        # Distance label below lanes
        label_y = layout["track_top"] + lanes_height + 6
        elements.append(_static(TextState(
            text=f"{dist}m",
            pos=Point2D(x, label_y),
            font_family=tc["marker_font_family"],
            font_size=tc["marker_font_size"],
            fill_color=Color(tc["marker_label_color"]),
            text_anchor="middle",
            dominant_baseline="hanging",
            z_index=-5.0,
        )))

    return elements


def create_finish_line(
    num_lanes: int,
    layout: dict,
    cfg: dict,
) -> VElement:
    """Create the finish line at 100m spanning lanes only."""
    tc = cfg["track"]
    lane_h = tc["lane_height"]
    lane_gap = tc["lane_gap"]
    x = distance_to_x(100.0, layout)

    lanes_height = num_lanes * lane_h + (num_lanes - 1) * lane_gap
    lanes_center_y = layout["track_top"] + lanes_height / 2

    return _static(LineState(
        pos=Point2D(x, lanes_center_y),
        length=lanes_height,
        rotation=90,
        stroke_color=Color(tc["finish_color"]),
        stroke_width=tc["finish_width"],
        stroke_opacity=tc["finish_opacity"],
        stroke_dasharray="4,3",
        z_index=-2.0,
    ))


def create_race_title(
    race: RaceData,
    layout: dict,
    cfg: dict,
) -> VElement:
    """Create the race title text above track area, left-aligned."""
    tc = cfg["title"]
    y = layout["track_top"] - tc["padding_above"]

    return _static(TextState(
        text=f"{race.year} {race.city}",
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
    race: RaceData,
    timing: dict,
    layout: dict,
    cfg: dict,
) -> VElement:
    """Create animated clock above track area using NumberState. Disappears when race ends."""
    cc = cfg["clock"]
    race_max_time = max(r.final_time for r in race.runners)
    race_start = timing["race_start"]
    total_duration = timing["total_duration"]
    race_finish_at = race_start + race_max_time / total_duration
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
                NumberState(value=race_max_time, **clock_base),
                NumberState(value=race_max_time, fill_opacity=0.0, **clock_base),
            ],
            at=race_finish_at,
        )
        .keystate(NumberState(value=race_max_time, fill_opacity=0.0, **clock_base), at=1.0)
    )


def create_track_elements(
    race: RaceData,
    timing: dict,
    cfg: dict,
) -> list[VElement]:
    """Create all track elements for a single race scene."""
    layout = _track_layout(cfg)
    num_lanes = len(race.runners)

    elements = []
    elements.extend(create_lane_backgrounds(num_lanes, layout, cfg))
    elements.extend(create_distance_markers(num_lanes, layout, cfg))
    elements.append(create_finish_line(num_lanes, layout, cfg))
    elements.append(create_race_title(race, layout, cfg))
    elements.append(create_clock_element(race, timing, layout, cfg))

    return elements
