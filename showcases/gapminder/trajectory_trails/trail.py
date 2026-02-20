"""Trajectory trail elements for Gapminder connected scatterplot.

Creates animated trails showing how countries travel through
GDP/life-expectancy space over time. Each country gets a PathState
trail drawn progressively, a moving marker, and a following label.
"""

import math

from coords import PlotConfig, gdp_to_x, life_exp_to_y
from data_prep import CountryDataPoint

from svan2d.component.state.circle import CircleState
from svan2d.component.state.path import PathState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement.velement import VElement


def _build_path_data(
    data_points: list[CountryDataPoint],
    config: PlotConfig,
) -> tuple[str, list[tuple[float, float]], list[float]]:
    """Build SVG path string and compute cumulative arc-length fractions.

    Returns:
        (path_string, xy_coords, arc_fractions) where arc_fractions[i] is
        the fraction of total arc length at data point i (0.0 to 1.0).
    """
    coords: list[tuple[float, float]] = []
    for point in data_points:
        coords.append((
            gdp_to_x(point.gdp_per_cap, config),
            life_exp_to_y(point.life_exp, config),
        ))

    # Build path string
    parts: list[str] = []
    for i, (x, y) in enumerate(coords):
        cmd = "M" if i == 0 else "L"
        parts.append(f"{cmd} {x:.2f},{y:.2f}")
    path_str = " ".join(parts)

    # Compute cumulative arc lengths
    cum_lengths = [0.0]
    for i in range(1, len(coords)):
        dx = coords[i][0] - coords[i - 1][0]
        dy = coords[i][1] - coords[i - 1][1]
        cum_lengths.append(cum_lengths[-1] + math.hypot(dx, dy))

    total = cum_lengths[-1]
    if total > 0:
        arc_fractions = [l / total for l in cum_lengths]
    else:
        arc_fractions = [i / (len(coords) - 1) for i in range(len(coords))]

    return path_str, coords, arc_fractions


def create_trail_elements(
    country_data: dict[str, list[CountryDataPoint]],
    continent_colors: dict[str, Color],
    config: PlotConfig,
    trail_cfg: dict,
    label_cfg: dict,
) -> tuple[list[VElement], list[VElement], list[VElement]]:
    """Create trail path, marker, and label VElements for each country.

    Args:
        country_data: Dictionary mapping country names to data points
        continent_colors: Mapping of continent to color
        config: PlotConfig for coordinate mapping
        trail_cfg: Trail styling config from TOML
        label_cfg: Label styling config from TOML

    Returns:
        Tuple of (path_elements, marker_elements, label_elements)
    """
    path_elements: list[VElement] = []
    marker_elements: list[VElement] = []
    label_elements: list[VElement] = []

    for country_name, data_points in country_data.items():
        if len(data_points) < 2:
            continue

        continent = data_points[0].continent
        color = continent_colors.get(continent, Color("#999999"))

        # --- Trail path: draw_progress with arc-length fractions ---
        # One keystate per data point. draw_progress uses arc length so
        # the trail tip matches the marker position at each keystate.
        path_str, coords, arc_fractions = _build_path_data(data_points, config)

        path_keystates: list[PathState] = []
        for i in range(len(data_points)):
            path_keystates.append(
                PathState(
                    data=path_str,
                    stroke_color=color,
                    stroke_width=trail_cfg["stroke_width"],
                    stroke_opacity=trail_cfg["stroke_opacity"],
                    stroke_linecap=trail_cfg["stroke_linecap"],
                    fill_color=Color.NONE,
                    draw_progress=arc_fractions[i],
                    z_index=0.5,
                )
            )

        path_elements.append(
            VElement()
            .keystates(states=path_keystates)
        )

        # --- Moving marker: follows trail tip through data points ---
        marker_keystates: list[CircleState] = []
        for i, point in enumerate(data_points):
            x, y = coords[i]
            marker_keystates.append(
                CircleState(
                    pos=Point2D(x, y),
                    radius=trail_cfg["marker_radius"],
                    fill_color=color,
                    stroke_color=Color(trail_cfg["marker_stroke_color"]),
                    stroke_width=trail_cfg["marker_stroke_width"],
                    z_index=2.0,
                )
            )

        marker_elements.append(
            VElement()
            .attributes(easing_dict={"pos": easing.linear})
            .keystates(states=marker_keystates)
        )

        # --- Label: follows marker ---
        label_keystates: list[TextState] = []
        for i, point in enumerate(data_points):
            x, y = coords[i]
            label_keystates.append(
                TextState(
                    text=country_name,
                    pos=Point2D(x + label_cfg["offset_x"], y),
                    font_family=label_cfg["font_family"],
                    font_size=label_cfg["font_size"],
                    font_weight=label_cfg["font_weight"],
                    fill_color=color,
                    text_anchor="start",
                    dominant_baseline="central",
                    z_index=3.0,
                )
            )

        label_elements.append(
            VElement()
            .attributes(easing_dict={"pos": easing.linear})
            .keystates(states=label_keystates)
        )

    return path_elements, marker_elements, label_elements
