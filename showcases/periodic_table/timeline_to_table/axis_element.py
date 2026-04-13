"""Axis line, tick marks, and tick labels for the timeline phase."""

from dataclasses import replace

from data_prep import AppData, TickData

from svan2d import (
    Color,
    easing,
    LineState,
    Point2D,
    RectangleState,
    TextState,
    VElement,
)


def _create_axis_line(
    data: AppData,
    axis_color: Color,
    axis_width: float,
    buildup_end: float,
    fly_end: float,
) -> VElement:
    """Axis line that grows from left, in sync with element appearances."""
    x_start = data.axis_x_start
    axis_length = data.axis_x_end - x_start
    cx = (x_start + data.axis_x_end) / 2
    y = data.axis_y

    # Full line (at buildup end)
    full = LineState(
        pos=Point2D(cx, y),
        length=axis_length,
        stroke_color=axis_color,
        stroke_width=axis_width,
    )

    # Start: zero length at left edge. Linear interpolation of pos+length
    # keeps the left endpoint fixed at axis_x_start.
    start = replace(full, pos=Point2D(x_start, y), length=0.0)
    faded = replace(full, opacity=0.0)

    last_cell_t = data.cells[-1].t_appear

    return (
        VElement()
        .keystate(start, at=0.0)
        .keystate(full, at=last_cell_t)
        .keystate(full, at=buildup_end)
        .transition(easing_dict={"opacity": easing.in_quad})
        .keystate(faded, at=fly_end)
        .keystate(faded, at=1.0)
    )


def _create_tick(
    tick: TickData,
    axis_y: float,
    tick_height: float,
    tick_color: Color,
    tick_font_size: float,
    tick_font_family: str,
    tick_label_color: Color,
    tick_label_offset: float,
    buildup_end: float,
    fly_end: float,
) -> list[VElement]:
    """Create tick mark (rectangle) and tick label (text) for one tick."""
    appear_dur = 0.005

    # Tick mark: thin rectangle below axis (Cartesian: below = smaller y)
    base_tick = RectangleState(
        pos=Point2D(tick.x_pos, axis_y - tick_height / 2),
        width=1.0,
        height=tick_height,
        fill_color=tick_color,
        opacity=0.0,
    )
    visible_tick = replace(base_tick, opacity=1.0)
    faded_tick = replace(base_tick, opacity=0.0)

    t_vis = min(tick.t_appear + appear_dur, buildup_end)
    tick_vel = (
        VElement()
        .keystate(base_tick, at=tick.t_appear)
        .transition(easing_dict={"opacity": easing.out_quad})
        .keystate(visible_tick, at=t_vis)
        .keystate(visible_tick, at=buildup_end)
        .transition(easing_dict={"opacity": easing.in_quad})
        .keystate(faded_tick, at=fly_end)
        .keystate(faded_tick, at=1.0)
    )

    # Tick label: year text below tick (Cartesian: below = smaller y)
    base_label = TextState(
        text=str(tick.year),
        pos=Point2D(tick.x_pos, axis_y - tick_height - tick_label_offset),
        font_size=tick_font_size,
        font_family=tick_font_family,
        fill_color=tick_label_color,
        opacity=0.0,
    )
    visible_label = replace(base_label, opacity=1.0)
    faded_label = replace(base_label, opacity=0.0)

    label_vel = (
        VElement()
        .keystate(base_label, at=tick.t_appear)
        .transition(easing_dict={"opacity": easing.out_quad})
        .keystate(visible_label, at=t_vis)
        .keystate(visible_label, at=buildup_end)
        .transition(easing_dict={"opacity": easing.in_quad})
        .keystate(faded_label, at=fly_end)
        .keystate(faded_label, at=1.0)
    )

    return [tick_vel, label_vel]


def create_axis_elements(
    data: AppData,
    axis_color: Color,
    axis_width: float,
    tick_height: float,
    tick_color: Color,
    tick_font_size: float,
    tick_font_family: str,
    tick_label_color: Color,
    tick_label_offset: float,
    buildup_end: float,
    fly_end: float,
) -> list[VElement]:
    """Create axis line + tick marks + tick labels."""
    elements: list[VElement] = []

    elements.append(
        _create_axis_line(data, axis_color, axis_width, buildup_end, fly_end)
    )

    for tick in data.ticks:
        elements.extend(
            _create_tick(
                tick,
                axis_y=data.axis_y,
                tick_height=tick_height,
                tick_color=tick_color,
                tick_font_size=tick_font_size,
                tick_font_family=tick_font_family,
                tick_label_color=tick_label_color,
                tick_label_offset=tick_label_offset,
                buildup_end=buildup_end,
                fly_end=fly_end,
            )
        )

    return elements
