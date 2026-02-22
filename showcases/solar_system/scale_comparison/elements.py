"""VElement builders for the planet scale comparison showcase."""

import math
from dataclasses import replace

from planets import PlanetData, SUN_RADIUS_KM
from scaling import scale_values

from svan2d.component.state.circle import CircleState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement.velement import VElement


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------


def _compute_x_positions(radii: list[float], min_gap: float) -> list[float]:
    """Centred x-positions so adjacent circles don't overlap."""
    n = len(radii)
    if n == 0:
        return []

    xs = [0.0]
    for i in range(1, n):
        xs.append(xs[i - 1] + radii[i - 1] + min_gap + radii[i])

    left_edge = xs[0] - radii[0]
    right_edge = xs[-1] + radii[-1]
    midpoint = (left_edge + right_edge) / 2
    return [x - midpoint for x in xs]


def _format_radius_km(km: float) -> str:
    return f"{km:,.0f} km"


# ---------------------------------------------------------------------------
# Element factories
# ---------------------------------------------------------------------------


def create_sun_element(cfg: dict) -> list[VElement]:
    """Sun circle + labels that slide in from above during phase 2."""
    scene_h = cfg["scene"]["height"]
    sun_cfg = cfg["sun"]
    label_cfg = cfg["planets"]["labels"]
    sun_radius = sun_cfg["radius_px"]
    sun_color = Color(sun_cfg["color"])
    padding_top = sun_cfg["padding_top"]
    phase2_start = cfg["animation"]["phase2_start"]
    phase2_end = cfg["animation"]["phase2_end"]
    offset_y = label_cfg["offset_y"]
    line_spacing = label_cfg.get("line_spacing", 14)

    # Final position: top of Sun near top of scene
    sun_center_y = -scene_h / 2 + sun_radius + padding_top

    # Hidden: centre far above so circle + labels are all off-screen
    label_extent = offset_y + line_spacing
    hidden_y = -(scene_h / 2 + sun_radius + label_extent)

    # Vertical offset from hidden to visible (labels slide the same amount)
    slide_dy = sun_center_y - hidden_y

    visible_state = CircleState(
        radius=sun_radius,
        pos=Point2D(0, sun_center_y),
        fill_color=sun_color,
        stroke_width=0,
    )
    hidden_state = replace(visible_state, pos=Point2D(0, hidden_y))

    circle_el = (
        VElement()
        .keystate(hidden_state, at=phase2_start)
        .transition(easing_dict={"pos": easing.in_out})
        .keystate(visible_state, at=phase2_end)
        .keystate(visible_state, at=1.0)
    )

    # Label positions: below the Sun circle
    label_y_visible = sun_center_y + sun_radius + offset_y + label_cfg["font_size"]
    label_y_hidden = label_y_visible - slide_dy
    font_color = Color(label_cfg["font_color"])
    easing_dict = {"pos": easing.in_out}

    # "Sun" name label
    name_visible = TextState(
        text="Sun",
        pos=Point2D(0, label_y_visible),
        font_family=label_cfg["font_family"],
        font_size=label_cfg["font_size"],
        fill_color=font_color,
        text_anchor="middle",
        dominant_baseline="auto",
        stroke_width=0,
    )
    name_hidden = replace(name_visible, pos=Point2D(0, label_y_hidden))
    name_el = (
        VElement()
        .keystate(name_hidden, at=phase2_start)
        .transition(easing_dict=easing_dict)
        .keystate(name_visible, at=phase2_end)
        .keystate(name_visible, at=1.0)
    )

    # Radius info label
    info_visible = TextState(
        text=_format_radius_km(SUN_RADIUS_KM),
        pos=Point2D(0, label_y_visible + line_spacing),
        font_family=label_cfg["font_family"],
        font_size=label_cfg["font_size"] - 1,
        fill_color=font_color,
        fill_opacity=0.6,
        text_anchor="middle",
        dominant_baseline="auto",
        stroke_width=0,
    )
    info_hidden = replace(info_visible, pos=Point2D(0, label_y_hidden + line_spacing))
    info_el = (
        VElement()
        .keystate(info_hidden, at=phase2_start)
        .transition(easing_dict=easing_dict)
        .keystate(info_visible, at=phase2_end)
        .keystate(info_visible, at=1.0)
    )

    return [circle_el, name_el, info_el]


def create_planet_elements(planets: list[PlanetData], cfg: dict) -> list[VElement]:
    """Planet circles: equal → true scale (phase 1), then shrink + move down (phase 2)."""
    size_cfg = cfg["planets"]["size"]
    sun_cfg = cfg["sun"]
    anim = cfg["animation"]
    min_gap_1 = cfg["layout"]["min_gap_1"]
    min_gap_2 = cfg["layout"]["min_gap_2"]
    min_gap_3 = cfg["layout"]["min_gap_3"]
    scene_h = cfg["scene"]["height"]

    equal_radius = size_cfg["equal_radius_px"]
    phase1_start = anim["phase1_start"]
    phase1_end = anim["phase1_end"]
    phase2_start = anim["phase2_start"]
    phase2_end = anim["phase2_end"]

    # Phase 1 radii + positions (at vertical centre)
    true_radii = scale_values(
        {p.name: p.radius_km for p in planets}, "linear", size_cfg["max_radius_px"]
    )
    equal_xs = _compute_x_positions([equal_radius] * len(planets), min_gap_1)
    true_xs = _compute_x_positions([true_radii[p.name] for p in planets], min_gap_2)

    # Phase 2 radii + positions (below the Sun)
    sun_radius_px = sun_cfg["radius_px"]
    sun_center_y = -scene_h / 2 + sun_radius_px + sun_cfg["padding_top"]
    planet_row_y = sun_center_y + sun_radius_px + sun_cfg["gap_to_planets"]

    phase2_all = {"Sun": SUN_RADIUS_KM}
    phase2_all.update({p.name: p.radius_km for p in planets})
    phase2_radii = scale_values(phase2_all, "linear", sun_radius_px)
    phase2_xs = _compute_x_positions([phase2_radii[p.name] for p in planets], min_gap_3)

    easing_dict = {"radius": easing.in_out, "pos": easing.in_out}

    elements: list[VElement] = []
    for i, p in enumerate(planets):
        color = Color(p.color)

        equal_state = CircleState(
            radius=equal_radius,
            pos=Point2D(equal_xs[i], 0.0),
            fill_color=color,
            stroke_width=0,
        )
        true_state = replace(
            equal_state,
            radius=true_radii[p.name],
            pos=Point2D(true_xs[i], 0.0),
        )
        final_state = replace(
            equal_state,
            radius=phase2_radii[p.name],
            pos=Point2D(phase2_xs[i], planet_row_y),
        )

        element = (
            VElement()
            .keystate(equal_state, at=0.0)
            .keystate(equal_state, at=phase1_start)
            .transition(easing_dict=easing_dict)
            .keystate(true_state, at=phase1_end)
            .keystate(true_state, at=phase2_start)
            .transition(easing_dict=easing_dict)
            .keystate(final_state, at=phase2_end)
            .keystate(final_state, at=1.0)
        )
        elements.append(element)

    return elements


def create_label_elements(planets: list[PlanetData], cfg: dict) -> list[VElement]:
    """Name + radius labels that track the bottom edge through all phases."""
    label_cfg = cfg["planets"]["labels"]
    if not label_cfg["show"]:
        return []

    size_cfg = cfg["planets"]["size"]
    sun_cfg = cfg["sun"]
    anim = cfg["animation"]
    min_gap_1 = cfg["layout"]["min_gap_1"]
    min_gap_2 = cfg["layout"]["min_gap_2"]
    min_gap_3 = cfg["layout"]["min_gap_3"]
    scene_h = cfg["scene"]["height"]

    equal_radius = size_cfg["equal_radius_px"]
    phase1_start = anim["phase1_start"]
    phase1_end = anim["phase1_end"]
    phase2_start = anim["phase2_start"]
    phase2_end = anim["phase2_end"]
    offset_y = label_cfg["offset_y"]
    line_spacing = label_cfg.get("line_spacing", 14)

    # Phase 1
    true_radii = scale_values(
        {p.name: p.radius_km for p in planets}, "linear", size_cfg["max_radius_px"]
    )
    equal_xs = _compute_x_positions([equal_radius] * len(planets), min_gap_1)
    true_xs = _compute_x_positions([true_radii[p.name] for p in planets], min_gap_2)

    # Phase 2
    sun_radius_px = sun_cfg["radius_px"]
    sun_center_y = -scene_h / 2 + sun_radius_px + sun_cfg["padding_top"]
    planet_row_y = sun_center_y + sun_radius_px + sun_cfg["gap_to_planets"]

    phase2_all = {"Sun": SUN_RADIUS_KM}
    phase2_all.update({p.name: p.radius_km for p in planets})
    phase2_radii = scale_values(phase2_all, "linear", sun_radius_px)
    phase2_xs = _compute_x_positions([phase2_radii[p.name] for p in planets], min_gap_3)

    easing_dict = {"pos": easing.in_out}

    # At 45° rotation, offset the info line perpendicular to the text direction
    # so it appears as a clean second line in the rotated frame.
    # Perpendicular (below) at 45°: dx = -sin(45°)*ls, dy = cos(45°)*ls
    sin45 = math.sin(math.radians(45))
    cos45 = math.cos(math.radians(45))
    ls_dx = -line_spacing * sin45
    ls_dy = line_spacing * cos45

    elements: list[VElement] = []
    for i, p in enumerate(planets):
        font_color = Color(label_cfg["font_color"])
        y_equal = equal_radius + offset_y
        y_true = true_radii[p.name] + offset_y
        y_final = planet_row_y + phase2_radii[p.name] + offset_y

        # --- Planet name (45° rotated) ---
        name_equal = TextState(
            text=p.name,
            pos=Point2D(equal_xs[i], y_equal),
            rotation=45,
            font_family=label_cfg["font_family"],
            font_size=label_cfg["font_size"],
            fill_color=font_color,
            text_anchor="start",
            dominant_baseline="auto",
            stroke_width=0,
        )
        name_true = replace(name_equal, pos=Point2D(true_xs[i], y_true))
        name_final = replace(name_equal, pos=Point2D(phase2_xs[i], y_final))

        name_el = (
            VElement()
            .keystate(name_equal, at=0.0)
            .transition(easing_dict=easing_dict)
            .keystate(name_equal, at=phase1_start)
            .transition(easing_dict=easing_dict)
            .keystate(name_true, at=phase1_end)
            .keystate(name_true, at=phase2_start)
            .transition(easing_dict=easing_dict)
            .keystate(name_final, at=phase2_end)
            .keystate(name_final, at=1.0)
        )
        elements.append(name_el)

        # --- Radius info (45° rotated, offset perpendicular to text) ---
        info_equal = TextState(
            text=_format_radius_km(p.radius_km),
            pos=Point2D(equal_xs[i] + ls_dx, y_equal + ls_dy),
            rotation=45,
            font_family=label_cfg["font_family"],
            font_size=label_cfg["font_size"] - 3,
            fill_color=font_color,
            fill_opacity=0,
            text_anchor="start",
            dominant_baseline="auto",
            stroke_width=0,
        )
        info_true = replace(
            info_equal,
            pos=Point2D(true_xs[i] + ls_dx, y_true + ls_dy),
            fill_opacity=0.6,
        )
        info_final = replace(
            info_true,
            pos=Point2D(phase2_xs[i] + ls_dx, y_final + ls_dy),
        )

        info_el = (
            VElement()
            .keystate(info_equal, at=phase1_start)
            .transition(easing_dict=easing_dict)
            .keystate(info_true, at=phase1_end)
            .keystate(info_true, at=phase2_start)
            .transition(easing_dict=easing_dict)
            .keystate(info_final, at=phase2_end)
            .keystate(info_final, at=1.0)
        )
        elements.append(info_el)

    return elements
