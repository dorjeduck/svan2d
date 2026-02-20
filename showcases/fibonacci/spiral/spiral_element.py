"""Spiral element for the Fibonacci Spiral showcase.

One VElement with draw_progress for smooth arc drawing.
Stroke width at each keystate = desired_px / camera_scale(t),
with log_lerp interpolation — exact match against the camera's
single exponential zoom curve.
"""

from typing import Callable

from data_prep import SpiralData
from svan2d.component.state.path import PathState, StrokeLinecap
from svan2d.core.color import Color
from svan2d.core.scalar_functions import log_lerp
from svan2d.velement.velement import VElement


def create_spiral_element(
    spiral: SpiralData,
    style_cfg: dict,
    scale_fn: Callable[[float], float],
) -> VElement:
    """Create the golden spiral with animated stroke width.

    stroke_width at each keystate = desired_px / scale_fn(t).
    log_lerp between keystates exactly matches the exponential camera zoom.
    """
    spiral_color = Color(style_cfg["spiral_color"])
    desired_px = style_cfg["spiral_width"]

    arc_times = spiral.arc_times
    n = len(arc_times)

    # Compute arc-length-based progress (proportional to fibonacci numbers)
    arc_geo = spiral.arc_geometry
    radii = [geo["arc_params"][2] for geo in arc_geo]
    total_length = sum(radii)
    cumulative = 0.0
    arc_progress = []
    for r in radii:
        cumulative += r
        arc_progress.append(cumulative / total_length)

    def make_state(progress: float, stroke_w: float) -> PathState:
        return PathState(
            data=spiral.path_data,
            stroke_color=spiral_color,
            stroke_width=stroke_w,
            stroke_linecap=StrokeLinecap.ROUND,
            fill_color=Color.NONE,
            draw_progress=progress,
        )

    interp = {"stroke_width": log_lerp}

    el = VElement()
    for i in range(n):
        t_start, t_end = arc_times[i]
        if i == 0:
            sw = desired_px / scale_fn(t_start)
            el = el.keystate(make_state(0.0, sw), at=t_start)
        el = el.transition(interpolation_dict=interp)
        sw = desired_px / scale_fn(t_end)
        el = el.keystate(make_state(arc_progress[i], sw), at=t_end)

    # Hold at full draw through end
    last_t_end = arc_times[-1][1]
    if last_t_end < 1.0:
        sw_final = desired_px / scale_fn(1.0)
        el = el.transition(interpolation_dict=interp)
        el = el.keystate(make_state(1.0, sw_final), at=1.0)
    return el
