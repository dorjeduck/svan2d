"""Animated runner elements for Olympic 100m Winners Race.

Creates circle and label VElements using svan2d's interpolation_dict
with PCHIP-based position functions from real split data.
Each runner has 6 keystates: lead-in, race start, finish, hold,
results position, results hold.
"""

from functools import partial

from svan2d.component.state.circle import CircleState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition.easing import in_out_cubic
from svan2d.velement.velement import VElement

from data_prep import RunnerSplitData, make_pos_interpolator
from track_elements import _track_layout, distance_to_x


def _lane_color(lane_idx: int, cfg: dict) -> Color:
    """Get lane color from config by index."""
    key = f"lane_{lane_idx}"
    return Color(cfg["runner"]["colors"][key])


def _lane_label(runner: RunnerSplitData) -> str:
    """Format lane label: "Bolt (JAM) - 2012" """
    last_name = runner.name.split()[-1]
    return f"{last_name} ({runner.country}) - {runner.year}"


def _results_target_y(placement: int, layout: dict, cfg: dict) -> float:
    """Compute Y position for a runner in results layout (ordered by placement)."""
    tc = cfg["track"]
    lane_h = tc["lane_height"]
    lane_gap = tc["lane_gap"]
    return layout["track_top"] + (placement - 1) * (lane_h + lane_gap) + lane_h / 2


def create_runner_elements(
    runners: list[RunnerSplitData],
    timing: dict,
    cfg: dict,
) -> tuple[list[VElement], list[VElement], list[VElement], list[VElement]]:
    """Create animated runner circles, name labels, finish times, and placement labels.

    Each element uses 6 keystates to animate through:
    lead-in → race → finish → hold → results transition → results hold
    """
    layout = _track_layout(cfg)
    rc = cfg["runner"]
    lc = rc["label"]
    fc = rc["finish_time"]
    pc = rc["placement"]
    res = rc["results"]
    tc = cfg["track"]

    lane_h = tc["lane_height"]
    lane_gap = tc["lane_gap"]

    race_start = timing["race_start"]
    results_start = timing["results_start"]
    results_end = timing["results_end"]
    total_duration = timing["total_duration"]

    dist_to_x = partial(distance_to_x, layout=layout)

    start_x = distance_to_x(0.0, layout)
    finish_x = distance_to_x(100.0, layout)

    # Placement column X: fixed position left of name labels
    w = cfg["scene"]["width"]
    placement_x = -w / 2 + tc["margin_left"] + pc["offset_x"]

    # Results X positions (relative to placement_x)
    results_label_x = placement_x + res["label_offset_x"]
    results_time_x = placement_x + res["time_offset_x"]

    easing_dict = {"pos": in_out_cubic}

    circle_elements = []
    label_elements = []
    finish_time_elements = []
    placement_elements = []

    for lane_idx, runner in enumerate(runners):
        y = layout["track_top"] + lane_idx * (lane_h + lane_gap) + lane_h / 2
        finish_at = race_start + runner.final_time / total_duration
        target_y = _results_target_y(runner.placement, layout, cfg)

        fill_color = _lane_color(lane_idx, cfg)

        # PCHIP interpolation function for pos
        pos_fn = make_pos_interpolator(runner, y, dist_to_x)

        # Label follows the same path but with offset
        label_pos_fn = make_pos_interpolator(
            runner,
            y + lc["offset_y"],
            lambda d, offset=lc["offset_x"]: distance_to_x(d, layout) + offset,
        )

        # --- Circle: 6 keystates ---
        circle_base = dict(
            radius=rc["radius"],
            fill_color=fill_color,
            fill_opacity=0.9,
            stroke_color=Color(rc["stroke_color"]),
            stroke_width=rc["stroke_width"],
            z_index=5.0,
        )
        circle_faded = dict(circle_base, radius=0, fill_opacity=0.0, stroke_width=0.0)
        circle_elements.append(
            VElement()
            .keystate(CircleState(pos=Point2D(start_x, y), **circle_base), at=0.0)
            .keystate(
                CircleState(pos=Point2D(start_x, y), **circle_base), at=race_start
            )
            .transition(interpolation_dict={"pos": pos_fn})
            .keystate(
                CircleState(pos=Point2D(finish_x, y), **circle_base), at=finish_at
            )
            .keystate(
                CircleState(pos=Point2D(finish_x, y), **circle_base), at=results_start
            )
            .keystate(
                CircleState(pos=Point2D(finish_x, y), **circle_faded), at=results_end
            )
            .keystate(CircleState(pos=Point2D(finish_x, y), **circle_faded), at=1.0)
        )

        # --- Label: 6 keystates ---
        label_text = _lane_label(runner)
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
        label_target_y = target_y + lc["offset_y"]

        # In results, label switches to start-anchored (right of circle)
        label_results_base = dict(label_base, text_anchor="start")

        label_elements.append(
            VElement()
            .keystate(
                TextState(pos=Point2D(label_start_x, label_y), **label_base), at=0.0
            )
            .keystate(
                TextState(pos=Point2D(label_start_x, label_y), **label_base),
                at=race_start,
            )
            .transition(interpolation_dict={"pos": label_pos_fn})
            .keystate(
                TextState(pos=Point2D(label_finish_x, label_y), **label_base),
                at=finish_at,
            )
            .keystate(
                TextState(pos=Point2D(label_finish_x, label_y), **label_base),
                at=results_start,
            )
            .transition(easing_dict=easing_dict)
            .keystate(
                TextState(
                    pos=Point2D(results_label_x, label_target_y), **label_results_base
                ),
                at=results_end,
            )
            .keystate(
                TextState(
                    pos=Point2D(results_label_x, label_target_y), **label_results_base
                ),
                at=1.0,
            )
        )

        # --- Finish time: invisible until crossing, then move to results row ---
        ft_x = finish_x + fc["offset_x"]
        finish_text = f"{runner.final_time:.2f}s"
        ft_base = dict(
            text=finish_text,
            font_family=fc["font_family"],
            font_size=fc["font_size"],
            font_weight=fc["font_weight"],
            fill_color=Color(fc["color"]),
            text_anchor="start",
            dominant_baseline="central",
            z_index=8.0,
        )
        ft_y = y + fc["offset_y"]
        ft_target_y = target_y + fc["offset_y"]

        finish_time_elements.append(
            VElement()
            .keystate(
                TextState(pos=Point2D(ft_x, ft_y), fill_opacity=0.0, **ft_base), at=0.0
            )
            .keystate(
                [
                    TextState(pos=Point2D(ft_x, ft_y), fill_opacity=0.0, **ft_base),
                    TextState(pos=Point2D(ft_x, ft_y), fill_opacity=1.0, **ft_base),
                ],
                at=finish_at,
            )
            .keystate(
                TextState(pos=Point2D(ft_x, ft_y), fill_opacity=1.0, **ft_base),
                at=results_start,
            )
            .transition(easing_dict=easing_dict)
            .keystate(
                TextState(
                    pos=Point2D(results_time_x, ft_target_y),
                    fill_opacity=1.0,
                    **ft_base,
                ),
                at=results_end,
            )
            .keystate(
                TextState(
                    pos=Point2D(results_time_x, ft_target_y),
                    fill_opacity=1.0,
                    **ft_base,
                ),
                at=1.0,
            )
        )

        # --- Placement rank: fade in at finish, move Y to results row ---
        pl_base = dict(
            text=f"#{runner.placement}",
            font_family=pc["font_family"],
            font_size=pc["font_size"],
            font_weight=pc["font_weight"],
            fill_color=Color(pc["color"]),
            text_anchor="end",
            dominant_baseline="central",
            z_index=8.0,
        )
        placement_elements.append(
            VElement()
            .keystate(
                TextState(pos=Point2D(placement_x, y), fill_opacity=0.0, **pl_base),
                at=0.0,
            )
            .keystate(
                [
                    TextState(pos=Point2D(placement_x, y), fill_opacity=0.0, **pl_base),
                    TextState(pos=Point2D(placement_x, y), fill_opacity=1.0, **pl_base),
                ],
                at=finish_at,
            )
            .keystate(
                TextState(pos=Point2D(placement_x, y), fill_opacity=1.0, **pl_base),
                at=results_start,
            )
            .transition(easing_dict=easing_dict)
            .keystate(
                TextState(
                    pos=Point2D(placement_x, target_y), fill_opacity=1.0, **pl_base
                ),
                at=results_end,
            )
            .keystate(
                TextState(
                    pos=Point2D(placement_x, target_y), fill_opacity=1.0, **pl_base
                ),
                at=1.0,
            )
        )

    return circle_elements, label_elements, finish_time_elements, placement_elements
