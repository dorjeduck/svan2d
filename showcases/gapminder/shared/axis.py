"""Static axes for Gapminder bubble chart.

Creates log-scale X axis (GDP), linear Y axis (Life Expectancy),
gridlines, tick labels, axis titles, and border lines.
All elements are static (single state, no animation).
"""

from dataclasses import dataclass

from svan2d.component.state.text import TextState
from svan2d.component.state.rectangle import RectangleState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement.velement import VElement

from bubble import BubbleConfig, gdp_to_x, life_exp_to_y


def _static(state) -> VElement:
    """Create a static VElement from a single state (needs two keystates for animation)."""
    return VElement().keystates(states=[state, state])


@dataclass
class AxisConfig:
    """Configuration for axes."""

    # Tick values
    gdp_ticks: list[float] | None = None  # Set in __post_init__ if None
    life_exp_ticks: list[float] | None = None  # Set in __post_init__ if None

    # Gridline styling
    gridline_color: Color = Color("#dddddd")
    gridline_width: float = 0.5
    gridline_opacity: float = 0.6

    # Border styling
    border_color: Color = Color("#999999")
    border_width: float = 0.8

    # Tick label styling
    font_family: str = "Arial"
    font_size: float = 9.0
    label_color: Color = Color("#666666")

    # Axis title styling
    title_font_family: str = "Arial"
    title_font_size: float = 11.0
    title_font_weight: str = "normal"
    title_color: Color = Color("#333333")
    x_title: str = "GDP per capita (PPP $, log scale)"
    y_title: str = "Life Expectancy (years)"

    def __post_init__(self):
        if self.gdp_ticks is None:
            self.gdp_ticks = [400, 1000, 4000, 16000, 64000]
        if self.life_exp_ticks is None:
            self.life_exp_ticks = [30, 40, 50, 60, 70, 80, 90]


def format_gdp_tick(value: float) -> str:
    """Format GDP tick value for display (e.g. $400, $1k, $16k)."""
    if value >= 1000:
        k = value / 1000
        if k == int(k):
            return f"${int(k)}k"
        return f"${k:.0f}k"
    return f"${int(value)}"


def create_axis_elements(
    bubble_config: BubbleConfig,
    axis_config: AxisConfig,
) -> list[VElement]:
    """Create all static axis VElements.

    Args:
        bubble_config: Bubble config (for coordinate mapping and plot bounds)
        axis_config: Axis styling configuration

    Returns:
        List of VElements for gridlines, tick labels, titles, and borders
    """
    elements: list[VElement] = []

    plot_left = bubble_config.plot_left
    plot_top = bubble_config.plot_top
    plot_bottom = bubble_config.plot_bottom
    plot_width = bubble_config.plot_width
    plot_height = bubble_config.plot_height

    gdp_ticks = axis_config.gdp_ticks or []
    life_exp_ticks = axis_config.life_exp_ticks or []

    # --- X axis (GDP) vertical gridlines and tick labels ---
    for gdp_val in gdp_ticks:
        x = gdp_to_x(gdp_val, bubble_config)

        # Vertical gridline
        elements.append(_static(RectangleState(
            pos=Point2D(x, plot_top + plot_height / 2),
            width=axis_config.gridline_width,
            height=plot_height,
            fill_color=axis_config.gridline_color,
            fill_opacity=axis_config.gridline_opacity,
            z_index=-10.0,
        )))

        # Tick label below plot
        elements.append(_static(TextState(
            text=format_gdp_tick(gdp_val),
            pos=Point2D(x, plot_bottom + 15),
            font_family=axis_config.font_family,
            font_size=axis_config.font_size,
            fill_color=axis_config.label_color,
            text_anchor="middle",
            dominant_baseline="hanging",
            z_index=-5.0,
        )))

    # --- Y axis (Life Expectancy) horizontal gridlines and tick labels ---
    for le_val in life_exp_ticks:
        y = life_exp_to_y(le_val, bubble_config)

        # Horizontal gridline
        elements.append(_static(RectangleState(
            pos=Point2D(plot_left + plot_width / 2, y),
            width=plot_width,
            height=axis_config.gridline_width,
            fill_color=axis_config.gridline_color,
            fill_opacity=axis_config.gridline_opacity,
            z_index=-10.0,
        )))

        # Tick label left of plot
        elements.append(_static(TextState(
            text=str(int(le_val)),
            pos=Point2D(plot_left - 8, y),
            font_family=axis_config.font_family,
            font_size=axis_config.font_size,
            fill_color=axis_config.label_color,
            text_anchor="end",
            dominant_baseline="central",
            z_index=-5.0,
        )))

    # --- Border lines (left edge + bottom edge) ---
    # Left border
    elements.append(_static(RectangleState(
        pos=Point2D(plot_left, plot_top + plot_height / 2),
        width=axis_config.border_width,
        height=plot_height,
        fill_color=axis_config.border_color,
        z_index=-5.0,
    )))

    # Bottom border
    elements.append(_static(RectangleState(
        pos=Point2D(plot_left + plot_width / 2, plot_bottom),
        width=plot_width,
        height=axis_config.border_width,
        fill_color=axis_config.border_color,
        z_index=-5.0,
    )))

    # --- Axis titles ---
    # X axis title (below tick labels)
    elements.append(_static(TextState(
        text=axis_config.x_title,
        pos=Point2D(plot_left + plot_width / 2, plot_bottom + 33),
        font_family=axis_config.title_font_family,
        font_size=axis_config.title_font_size,
        font_weight=axis_config.title_font_weight,
        fill_color=axis_config.title_color,
        text_anchor="middle",
        dominant_baseline="hanging",
        z_index=-5.0,
    )))

    # Y axis title (left of tick labels, rotated)
    # Note: SVG rotation not supported via TextState directly,
    # so we place it vertically as a horizontal label
    elements.append(_static(TextState(
        text=axis_config.y_title,
        pos=Point2D(plot_left - 40, plot_top + plot_height / 2),
        font_family=axis_config.title_font_family,
        font_size=axis_config.title_font_size,
        font_weight=axis_config.title_font_weight,
        fill_color=axis_config.title_color,
        text_anchor="middle",
        dominant_baseline="central",
        rotation=-90,
        z_index=-5.0,
    )))

    return elements
