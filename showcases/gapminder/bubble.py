"""Bubble elements for Gapminder bubble chart.

Creates animated bubble (CircleState) and label (TextState) VElements
with log-scale GDP x-axis, linear life expectancy y-axis, and
sqrt-proportional population radius.
"""

import math
from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.circle import CircleRenderer
from svan2d.component.state.circle import CircleState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement.velement import VElement

from data_prep import CountryDataPoint


@renderer(CircleRenderer)
@dataclass(frozen=True)
class BubbleState(CircleState):
    """Circle state extended with gapminder metadata."""

    country_name: str = ""
    continent: str = ""
    year: float = 0
    gdp_per_cap: float = 0
    life_exp: float = 0
    population: float = 0


@dataclass
class BubbleConfig:
    """Configuration for bubble layout and styling."""

    # Plot area bounds (centered origin)
    plot_left: float = -425.0
    plot_right: float = 460.0
    plot_top: float = -250.0
    plot_bottom: float = 225.0

    # GDP log scale range
    gdp_min: float = 200.0
    gdp_max: float = 120000.0

    # Life expectancy linear range
    life_exp_min: float = 20.0
    life_exp_max: float = 90.0

    # Bubble radius range
    radius_min: float = 2.0
    radius_max: float = 40.0
    radius_reference_pop: float = 1_400_000_000.0

    # Styling
    fill_opacity: float = 0.75
    stroke_color: Color = Color("#ffffff")
    stroke_width: float = 0.5
    stroke_opacity: float = 0.8

    # Label styling
    label_font_family: str = "Arial"
    label_font_size: float = 8.0
    label_font_weight: str = "normal"
    label_color: Color = Color("#333333")
    label_offset_y: float = -5.0

    @property
    def plot_width(self) -> float:
        return self.plot_right - self.plot_left

    @property
    def plot_height(self) -> float:
        return self.plot_bottom - self.plot_top


def gdp_to_x(gdp: float, config: BubbleConfig) -> float:
    """Map GDP per capita to X coordinate using log10 scale."""
    log_min = math.log10(config.gdp_min)
    log_max = math.log10(config.gdp_max)
    log_gdp = math.log10(max(config.gdp_min, gdp))
    t = (log_gdp - log_min) / (log_max - log_min)
    return config.plot_left + t * config.plot_width


def life_exp_to_y(life_exp: float, config: BubbleConfig) -> float:
    """Map life expectancy to Y coordinate (higher life exp = up = lower Y in center origin)."""
    t = (life_exp - config.life_exp_min) / (config.life_exp_max - config.life_exp_min)
    # Invert: higher life_exp maps to plot_top (negative Y)
    return config.plot_bottom - t * config.plot_height


def population_to_radius(pop: float, config: BubbleConfig) -> float:
    """Map population to bubble radius using sqrt scaling."""
    ratio = pop / config.radius_reference_pop
    r = config.radius_max * math.sqrt(ratio)
    return max(config.radius_min, min(config.radius_max, r))


def create_bubble_state(
    point: CountryDataPoint,
    continent_colors: dict[str, Color],
    config: BubbleConfig,
) -> BubbleState:
    """Create a BubbleState for a single data point."""
    x = gdp_to_x(point.gdp_per_cap, config)
    y = life_exp_to_y(point.life_exp, config)
    r = population_to_radius(point.population, config)

    return BubbleState(
        pos=Point2D(x, y),
        radius=r,
        country_name=point.country,
        continent=point.continent,
        year=point.year,
        gdp_per_cap=point.gdp_per_cap,
        life_exp=point.life_exp,
        population=point.population,
        fill_color=continent_colors.get(point.continent, Color("#999999")),
        fill_opacity=config.fill_opacity,
        stroke_color=config.stroke_color,
        stroke_width=config.stroke_width,
        stroke_opacity=config.stroke_opacity,
        # Smaller bubbles on top (higher z_index)
        z_index=1.0 / max(1.0, point.population),
    )


def create_label_state(
    point: CountryDataPoint,
    config: BubbleConfig,
) -> TextState:
    """Create a TextState label for a bubble."""
    x = gdp_to_x(point.gdp_per_cap, config)
    y = life_exp_to_y(point.life_exp, config)
    r = population_to_radius(point.population, config)

    return TextState(
        text=point.country,
        pos=Point2D(x, y - r + config.label_offset_y),
        font_family=config.label_font_family,
        font_size=config.label_font_size,
        font_weight=config.label_font_weight,
        fill_color=config.label_color,
        text_anchor="middle",
        dominant_baseline="auto",
        z_index=10.0,
    )


def create_bubble_elements(
    country_data: dict[str, list[CountryDataPoint]],
    continent_colors: dict[str, Color],
    config: BubbleConfig,
    labeled_countries: set[str],
) -> tuple[list[VElement], list[VElement]]:
    """Create all bubble and label VElements.

    Args:
        country_data: Dictionary mapping country names to data points
        continent_colors: Mapping of continent to fill color
        config: Bubble chart configuration
        labeled_countries: Set of country names that get text labels

    Returns:
        Tuple of (bubble_elements, label_elements)
    """
    all_bubble_states: list[list[BubbleState]] = []
    all_label_states: list[list[TextState]] = []

    for country_name, data_points in country_data.items():
        bubble_keystates = []
        label_keystates = [] if country_name in labeled_countries else None

        for point in data_points:
            bubble_keystates.append(
                create_bubble_state(point, continent_colors, config)
            )
            if label_keystates is not None:
                label_keystates.append(create_label_state(point, config))

        all_bubble_states.append(bubble_keystates)
        if label_keystates is not None:
            all_label_states.append(label_keystates)

    bubble_elements = [
        VElement()
        .attributes(easing_dict={"pos": easing.linear})
        .keystates(states=keystates)
        for keystates in all_bubble_states
    ]

    label_elements = [
        VElement()
        .attributes(easing_dict={"pos": easing.linear})
        .keystates(states=keystates)
        for keystates in all_label_states
    ]

    return bubble_elements, label_elements
