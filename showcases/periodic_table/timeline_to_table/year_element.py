"""Large background year label for the timeline phase.

Font size is divided by the camera scale at each keystate so the label
appears at a consistent visual size regardless of zoom level.
"""

from dataclasses import replace
from typing import Callable

from data_prep import AppData

from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement.velement import VElement


def create_year_element(
    data: AppData,
    font_family: str,
    font_size: float,
    font_weight: str,
    fill_color: Color,
    fill_opacity: float,
    buildup_end: float,
    fly_end: float,
    scale_func: Callable[[float], float],
    offset_func: Callable[[float], Point2D],
) -> VElement:
    """Create a large background year label that tracks the camera during buildup.

    The font_size at each keystate is base_font_size / camera_scale so it
    appears at a constant visual size on screen.
    """
    tl_cell = data.tl_cell_size

    vel = VElement()
    last_state: TextState | None = None

    seen_years: set[int] = set()
    for cell in data.cells:
        year = cell.element.discovery_year
        if year in seen_years:
            continue
        seen_years.add(year)

        t = cell.t_appear
        cam_scale = scale_func(t)
        cam_pos = offset_func(t)

        # Position above the cells in camera-centered coordinates
        visual_font = font_size / cam_scale
        label_y = cam_pos.y - tl_cell / 2 - visual_font * 1.2

        label = f"{abs(year)} BCE" if year < 0 else str(year)
        state = TextState(
            text=label,
            pos=Point2D(cam_pos.x, label_y),
            font_size=font_size / cam_scale,
            font_family=font_family,
            font_weight=font_weight,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
        )
        vel = vel.keystate(state, at=t)
        last_state = state

    # Hold last year at buildup_end, then fade out
    assert last_state is not None
    vel = vel.keystate(last_state, at=buildup_end)
    faded = replace(last_state, fill_opacity=0.0, opacity=0.0)
    vel = (
        vel.transition(
            easing_dict={"fill_opacity": easing.in_quad, "opacity": easing.in_quad}
        )
        .keystate(faded, at=fly_end)
        .keystate(faded, at=1.0)
    )

    return vel
