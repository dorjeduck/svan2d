"""Square elements for the Fibonacci Spiral showcase.

Each square fades in during its time window, with stroke_width
derived from the camera's exponential scale function. log_lerp
interpolation is exact against the single exponential zoom.
"""

from dataclasses import replace
from typing import Callable

from data_prep import FibonacciData
from svan2d.component.state.rectangle import RectangleState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.scalar_functions import log_lerp
from svan2d.velement.velement import VElement


def create_square_elements(
    data: FibonacciData,
    style_cfg: dict,
    scale_fn: Callable[[float], float],
) -> list[VElement]:
    """Create VElements for each Fibonacci square with opacity fade-in.

    Stroke width at each keystate = desired_sw / scale_fn(t).
    log_lerp between keystates exactly matches the exponential camera zoom.
    """
    squares = data.squares
    colors = [Color(c) for c in style_cfg["colors"]]
    fill_opacity = style_cfg["square_fill_opacity"]
    stroke_opacity = style_cfg["square_stroke_opacity"]
    desired_sw = style_cfg["square_stroke_width"]
    stroke_color = Color(style_cfg["square_stroke_color"])
    label_opacity = style_cfg["label_opacity"]
    label_color = Color(style_cfg["label_color"])
    show_labels = style_cfg["show_labels"]

    stroke_interp = {"stroke_width": log_lerp}
    elements = []

    for sq in squares:
        color = colors[sq.index % len(colors)]
        sw_start = desired_sw / scale_fn(sq.t_start)
        sw_end = desired_sw / scale_fn(sq.t_end)
        sw_final = desired_sw / scale_fn(1.0)

        state_hidden = RectangleState(
            width=sq.size,
            height=sq.size,
            pos=sq.center,
            fill_color=color,
            fill_opacity=0.0,
            stroke_color=stroke_color,
            stroke_width=sw_start,
            stroke_opacity=0.0,
        )
        state_visible = replace(
            state_hidden,
            fill_opacity=fill_opacity,
            stroke_width=sw_end,
            stroke_opacity=stroke_opacity,
        )

        el = VElement().keystate(state_hidden, at=sq.t_start)
        el = el.transition(interpolation_dict=stroke_interp)
        el = el.keystate(state_visible, at=sq.t_end)
        if sq.t_end < 1.0:
            state_final = replace(state_visible, stroke_width=sw_final)
            el = el.transition(interpolation_dict=stroke_interp)
            el = el.keystate(state_final, at=1.0)
        elements.append(el)

        if show_labels:
            font_size = sq.size * 0.3
            label_hidden = TextState(
                text=str(sq.fib_value),
                pos=sq.center,
                font_size=font_size,
                font_family="Arial",
                font_weight="bold",
                fill_color=label_color,
                opacity=0.0,
            )
            label_visible = replace(label_hidden, opacity=label_opacity)
            label_el = VElement().keystate(label_hidden, at=sq.t_start)
            label_el = label_el.keystate(label_visible, at=sq.t_end)
            if sq.t_end < 1.0:
                label_el = label_el.keystate(label_visible, at=1.0)
            elements.append(label_el)

    return elements
