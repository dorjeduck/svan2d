"""Continent color legend for Gapminder bubble chart."""

from dataclasses import dataclass

from svan2d.component.state.circle import CircleState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement.velement import VElement


def _static(state) -> VElement:
    """Create a static VElement from a single state (needs two keystates for animation)."""
    return VElement().keystates(states=[state, state])


@dataclass
class LegendConfig:
    """Configuration for the continent legend."""

    # Position offsets from top-right corner of plot area
    offset_right: float = 10.0
    offset_top: float = 5.0

    # Swatch styling
    swatch_radius: float = 5.0
    swatch_gap: float = 14.0  # Vertical gap between items

    # Label styling
    label_offset_x: float = 10.0  # From swatch center to label start
    font_family: str = "Arial"
    font_size: float = 9.0
    font_color: Color = Color("#333333")


def create_legend_elements(
    continent_colors: dict[str, Color],
    plot_right: float,
    plot_top: float,
    config: LegendConfig,
) -> list[VElement]:
    """Create static legend VElements.

    Args:
        continent_colors: Mapping of continent name to color
        plot_right: Right edge of plot area
        plot_top: Top edge of plot area
        config: Legend configuration

    Returns:
        List of VElements (swatch circles + text labels)
    """
    elements: list[VElement] = []

    x_swatch = plot_right - config.offset_right
    y_start = plot_top + config.offset_top + config.swatch_radius

    for i, (continent, color) in enumerate(continent_colors.items()):
        y = y_start + i * config.swatch_gap

        # Color swatch (small filled circle)
        elements.append(_static(CircleState(
            pos=Point2D(x_swatch, y),
            radius=config.swatch_radius,
            fill_color=color,
            fill_opacity=0.85,
            z_index=5.0,
        )))

        # Continent label
        elements.append(_static(TextState(
            text=continent,
            pos=Point2D(x_swatch - config.label_offset_x, y),
            font_family=config.font_family,
            font_size=config.font_size,
            fill_color=config.font_color,
            text_anchor="end",
            dominant_baseline="central",
            z_index=5.0,
        )))

    return elements
