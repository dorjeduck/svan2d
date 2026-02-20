"""Animated runner elements for 100m Sprint Race Replay.

Creates circle and label VElements using svan2d's interpolation_dict
with PCHIP-based position functions from real split data.
Each runner has 4 keystates: lead-in hold, race start, finish, end hold.
"""

from functools import partial

from svan2d.component.state.circle import CircleState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement.velement import VElement

from data_prep import RaceData, make_pos_interpolator
from track_elements import _track_layout, distance_to_x


# Lane color keys in order
_LANE_COLOR_KEYS = ["lane_1", "lane_2", "lane_3"]


def create_runner_elements(
    race: RaceData,
    timing: dict,
    cfg: dict,
) -> tuple[list[VElement], list[VElement], list[VElement]]:
    """Create animated runner circles, name labels, and finish time labels.

    Args:
        race: Race data with runner splits
        timing: Timeline mapping (race_start, total_duration, max_time)
        cfg: Configuration dictionary

    Returns:
        Tuple of (circle_elements, label_elements, finish_time_elements)
    """
    layout = _track_layout(cfg)
    rc = cfg["runner"]
    lc = rc["label"]
    fc = rc["finish_time"]
    tc = cfg["track"]

    lane_h = tc["lane_height"]
    lane_gap = tc["lane_gap"]

    race_start = timing["race_start"]
    total_duration = timing["total_duration"]

    dist_to_x = partial(distance_to_x, layout=layout)

    start_x = distance_to_x(0.0, layout)
    finish_x = distance_to_x(100.0, layout)

    circle_elements = []
    label_elements = []
    finish_time_elements = []

    for lane_idx, runner in enumerate(race.runners):
        y = layout["track_top"] + lane_idx * (lane_h + lane_gap) + lane_h / 2
        finish_at = race_start + runner.final_time / total_duration

        color_key = _LANE_COLOR_KEYS[lane_idx] if lane_idx < len(_LANE_COLOR_KEYS) else "lane_1"
        fill_color = Color(rc["colors"][color_key])

        # PCHIP interpolation function for pos
        pos_fn = make_pos_interpolator(runner, y, dist_to_x)

        # Label follows the same path but with offset
        label_pos_fn = make_pos_interpolator(
            runner, y + lc["offset_y"],
            lambda d, offset=lc["offset_x"]: distance_to_x(d, layout) + offset,
        )

        # --- Circle: 4 keystates ---
        circle_base = dict(
            radius=rc["radius"],
            fill_color=fill_color,
            fill_opacity=0.9,
            stroke_color=Color(rc["stroke_color"]),
            stroke_width=rc["stroke_width"],
            z_index=5.0,
        )
        circle_elements.append(
            VElement()
            .keystate(CircleState(pos=Point2D(start_x, y), **circle_base), at=0.0)
            .keystate(CircleState(pos=Point2D(start_x, y), **circle_base), at=race_start)
            .transition(interpolation_dict={"pos": pos_fn})
            .keystate(CircleState(pos=Point2D(finish_x, y), **circle_base), at=finish_at)
            .keystate(CircleState(pos=Point2D(finish_x, y), **circle_base), at=1.0)
        )

        # --- Label: 4 keystates ---
        label_text = f"{runner.name} ({runner.country})"
        label_base = dict(
            text=label_text,
            font_family=lc["font_family"],
            font_size=lc["font_size"],
            font_weight=lc["font_weight"],
            fill_color=Color(lc["color"]),
            text_anchor="end",
            dominant_baseline="central",
            z_index=6.0,
        )
        label_start_x = start_x + lc["offset_x"]
        label_finish_x = finish_x + lc["offset_x"]
        label_y = y + lc["offset_y"]

        label_elements.append(
            VElement()
            .keystate(TextState(pos=Point2D(label_start_x, label_y), **label_base), at=0.0)
            .keystate(TextState(pos=Point2D(label_start_x, label_y), **label_base), at=race_start)
            .transition(interpolation_dict={"pos": label_pos_fn})
            .keystate(TextState(pos=Point2D(label_finish_x, label_y), **label_base), at=finish_at)
            .keystate(TextState(pos=Point2D(label_finish_x, label_y), **label_base), at=1.0)
        )

        # --- Finish time: invisible until crossing, then visible ---
        ft_x = finish_x + fc["offset_x"]
        ft_base = dict(
            text=f"{runner.final_time:.2f}s",
            pos=Point2D(ft_x, y + fc["offset_y"]),
            font_family=fc["font_family"],
            font_size=fc["font_size"],
            font_weight=fc["font_weight"],
            fill_color=Color(fc["color"]),
            text_anchor="start",
            dominant_baseline="central",
            z_index=8.0,
        )
        finish_time_elements.append(
            VElement()
            .keystate(TextState(fill_opacity=0.0, **ft_base), at=0.0)
            .keystate(
                [TextState(fill_opacity=0.0, **ft_base), TextState(fill_opacity=1.0, **ft_base)],
                at=finish_at,
            )
            .keystate(TextState(fill_opacity=1.0, **ft_base), at=1.0)
        )

    return circle_elements, label_elements, finish_time_elements
