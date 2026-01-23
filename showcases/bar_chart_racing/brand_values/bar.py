"""Bar elements for bar chart race animation.

Creates animated bars with company name labels and value displays.
"""

from collections import namedtuple
from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.rectangle import RectangleRenderer
from svan2d.component.state.number import NumberFormat, NumberState
from svan2d.component.state.rectangle import RectangleState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement.velement import VElement

from data_prep import CompanyDataPoint


@renderer(RectangleRenderer)
@dataclass(frozen=True)
class BarState(RectangleState):
    """Rectangle state extended with bar chart metadata."""

    company_name: str = ""
    category: str = ""
    value: float = 0
    rank: int = 0
    year: float = 0


LabelStates = namedtuple("LabelStates", ["company_name", "value"])


@dataclass
class BarConfig:
    """Configuration for bar chart layout."""

    # Plot area bounds (in scene coordinates)
    plot_left: float = -245.0
    plot_right: float = 245.0
    plot_top: float = -225.0
    plot_bottom: float = 240.0

    # Bar dimensions
    bar_height: float = 42.0
    bar_margin: float = 6.0
    top_n: int = 10

    # Bar styling
    fill_opacity: float = 0.75

    # Label styling
    name_font_family: str = "Inter"
    name_font_size: int = 10
    name_font_weight: str = "bold"
    name_color: Color = Color("#000033")
    value_font_family: str = "IBM Plex Mono"
    value_font_size: int = 9
    value_font_weight: str = "normal"
    value_color: Color = Color("#000033")
    label_gap: float = 2.0  # Gap between name and value labels

    # Off-screen position for bars outside top_n (calculated if None)
    offscreen_y: float | None = None

    def __post_init__(self):

        if self.offscreen_y is None:
            # Position just below the visible plot area
            self.offscreen_y = self.plot_bottom + self.bar_height

    @property
    def bar_width(self) -> float:
        """Maximum bar width based on plot area."""
        return self.plot_right - self.plot_left

    @property
    def bar_slot_height(self) -> float:
        """Height allocated per bar including margin."""
        return self.bar_height + self.bar_margin


def create_bar_state(
    data_point: CompanyDataPoint,
    category_colors: dict[str, Color],
    config: BarConfig,
) -> BarState:
    """Create a bar state for a single data point.

    Args:
        data_point: Company data at a specific time
        category_colors: Mapping of category to fill color
        config: Bar chart configuration

    Returns:
        BarState positioned and sized appropriately
    """
    bar_width = max(1, config.bar_width * data_point.ratio_of_top)

    # X position: left edge + half bar width (centered on left edge)
    x = config.plot_left + bar_width / 2

    # Y position: based on rank
    if data_point.rank <= config.top_n:
        y = config.plot_top + (data_point.rank - 0.5) * config.bar_slot_height
    else:
        # offscreen_y is set in __post_init__ if None
        y = config.offscreen_y if config.offscreen_y is not None else config.plot_bottom + config.bar_height

    return BarState(
        pos=Point2D(x, y),
        company_name=data_point.name,
        category=data_point.category,
        value=data_point.value,
        year=data_point.year,
        rank=data_point.rank,
        fill_color=category_colors[data_point.category],
        fill_opacity=config.fill_opacity,
        width=bar_width,
        height=config.bar_height,
    )


def create_label_states(
    data_point: CompanyDataPoint,
    config: BarConfig,
) -> LabelStates:
    """Create label states (company name and value) for a data point.

    Args:
        data_point: Company data at a specific time
        config: Bar chart configuration

    Returns:
        LabelStates tuple with name and value TextStates
    """
    bar_width = max(1, config.bar_width * data_point.ratio_of_top)
    label_x = config.plot_left + bar_width - 5

    if data_point.rank <= config.top_n:
        label_y = config.plot_top + (data_point.rank - 0.5) * config.bar_slot_height
    else:
        label_y = config.offscreen_y if config.offscreen_y is not None else config.plot_bottom + config.bar_height

    # Calculate vertical offsets based on font sizes
    # Name above center, value below center, with gap between them
    half_gap = config.label_gap / 2
    name_y_offset = -(config.value_font_size * 0.5 + half_gap)
    value_y_offset = config.name_font_size * 0.5 + half_gap

    name_state = TextState(
        text=data_point.name,
        pos=Point2D(label_x, label_y + name_y_offset),
        font_family=config.name_font_family,
        font_size=config.name_font_size,
        font_weight=config.name_font_weight,
        fill_color=config.name_color,
        text_anchor="end",
        z_index=2,
    )

    value_state = NumberState(
        value=data_point.value,
        pos=Point2D(label_x, label_y + value_y_offset),
        format=NumberFormat.INTEGER,
        thousands_separator=",",
        font_family=config.value_font_family,
        font_size=config.value_font_size,
        font_weight=config.value_font_weight,
        fill_color=config.value_color,
        text_anchor="end",
        z_index=2,
    )

    return LabelStates(name_state, value_state)


def create_bar_elements(
    company_data: dict[str, list[CompanyDataPoint]],
    category_colors: dict[str, Color],
    config: BarConfig | None = None,
) -> tuple[list[VElement], list[VElement], list[VElement]]:
    """Create all bar and label VElements.

    Args:
        company_data: Dictionary mapping company names to data points
        category_colors: Mapping of category to fill color
        config: Bar chart configuration (uses defaults if None)

    Returns:
        Tuple of (bar_elements, name_elements, value_elements)
    """
    if config is None:
        config = BarConfig()

    all_bar_states = []
    all_name_states = []
    all_value_states = []

    for company_name, data_points in company_data.items():
        bar_keystates = []
        name_keystates = []
        value_keystates = []

        for point in data_points:
            bar_keystates.append(create_bar_state(point, category_colors, config))

            labels = create_label_states(point, config)
            name_keystates.append(labels.company_name)
            value_keystates.append(labels.value)

        all_bar_states.append(bar_keystates)
        all_name_states.append(name_keystates)
        all_value_states.append(value_keystates)

    bar_elements = [
        VElement()
        .attributes(easing_dict={"pos": easing.linear})
        .keystates(states=keystates)
        for keystates in all_bar_states
    ]

    name_elements = [
        VElement()
        .attributes(easing_dict={"pos": easing.linear})
        .keystates(states=keystates)
        for keystates in all_name_states
    ]

    value_elements = [
        VElement()
        .attributes(easing_dict={"pos": easing.linear})
        .keystates(states=keystates)
        for keystates in all_value_states
    ]

    return bar_elements, name_elements, value_elements
