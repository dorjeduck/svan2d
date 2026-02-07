"""Dynamic value axis for bar chart race animation.

Creates tick marks that slide horizontally as the scale changes,
with automatic interval adjustment and fade transitions.
"""

import math
from dataclasses import dataclass

from svan2d.component.state.text import TextState
from svan2d.component.state.rectangle import RectangleState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement.velement import VElement


def get_tick_interval(max_value: float, target_tick_count: int = 5) -> float:
    """Return a round interval (1, 2, 5, 10, 20, 50...) for the given max.

    Args:
        max_value: The maximum value to create ticks for
        target_tick_count: Approximate number of ticks desired

    Returns:
        A round interval value
    """
    if max_value <= 0:
        return 1.0

    rough_interval = max_value / target_tick_count
    magnitude = 10 ** math.floor(math.log10(rough_interval))
    residual = rough_interval / magnitude

    if residual <= 1.5:
        multiplier = 1
    elif residual <= 3:
        multiplier = 2
    elif residual <= 7:
        multiplier = 5
    else:
        multiplier = 10

    return multiplier * magnitude


def get_all_tick_values(
    max_values: list[float], target_tick_count: int = 5
) -> set[float]:
    """Find all unique tick values needed across the animation.

    Args:
        max_values: List of maximum values, one per frame
        target_tick_count: Approximate number of ticks desired per frame

    Returns:
        Set of all tick values that will be needed
    """
    all_ticks = set()

    for max_val in max_values:
        if max_val <= 0:
            continue
        interval = get_tick_interval(max_val, target_tick_count)
        tick_val = 0.0
        while tick_val <= max_val:
            all_ticks.add(tick_val)
            tick_val += interval

    return all_ticks


def is_tick_visible(
    tick_value: float, max_value: float, target_tick_count: int = 5
) -> bool:
    """Check if a tick value should be visible given current max.

    Args:
        tick_value: The tick value to check
        max_value: Current maximum value
        target_tick_count: Approximate number of ticks desired

    Returns:
        True if tick should be visible
    """
    if max_value <= 0:
        return tick_value == 0
    if tick_value > max_value:
        return False

    interval = get_tick_interval(max_value, target_tick_count)

    # Use tolerance for floating point comparison
    remainder = tick_value % interval
    tolerance = interval * 1e-9
    return remainder < tolerance or (interval - remainder) < tolerance


def format_tick_value(value: float) -> str:
    """Format a tick value for display with thousands separators.

    Args:
        value: The value to format (in millions)

    Returns:
        Formatted string with commas (e.g., "50,000")
    """
    return f"{value:,.0f}"


@dataclass
class AxisConfig:
    """Configuration for the value axis."""

    left_x: float = -200.0
    width: float = 400.0
    label_y: float = -220.0
    line_top_y: float = -210.0
    line_height: float = 430.0
    target_tick_count: int = 5
    font_family: str = "IBM Plex Mono"
    font_size: int = 8
    label_color: Color = Color(0, 0, 0)
    line_color: Color = Color(0, 0, 0)
    line_width: float = 1.0
    line_opacity: float = 0.3
    zero_line_color: Color = Color(0, 0, 0)
    zero_line_width: float = 1.0

    def __post_init__(self):
        if self.label_color is None:
            self.label_color = Color("#333333")
        if self.line_color is None:
            self.line_color = Color("#999999")
        if self.zero_line_color is None:
            self.zero_line_color = Color("#666666")


def create_tick_label_state(
    value: float,
    x: float,
    y: float,
    opacity: float,
    config: AxisConfig,
) -> TextState:
    """Create a tick label state.

    Args:
        value: The tick value
        x: X position
        y: Y position
        opacity: Fill opacity (0-1)
        config: Axis configuration

    Returns:
        TextState for the label
    """
    return TextState(
        text=format_tick_value(value),
        pos=Point2D(x, y),
        fill_opacity=opacity,
        fill_color=config.label_color,
        font_family=config.font_family,
        font_size=config.font_size,
        text_anchor="middle",
    )


def create_tick_line_state(
    x: float,
    top_y: float,
    height: float,
    opacity: float,
    config: AxisConfig,
    is_zero: bool = False,
) -> RectangleState:
    """Create a tick line state.

    Args:
        x: X position (center of line)
        top_y: Top Y position
        height: Line height
        opacity: Fill opacity (0-1)
        config: Axis configuration
        is_zero: Whether this is the zero/y-axis line

    Returns:
        RectangleState for the line
    """
    if is_zero:
        return RectangleState(
            pos=Point2D(x, top_y + height / 2),
            width=config.zero_line_width,
            height=height,
            fill_color=config.zero_line_color,
            fill_opacity=opacity,
        )
    else:
        return RectangleState(
            pos=Point2D(x, top_y + height / 2),
            width=config.line_width,
            height=height,
            fill_color=config.line_color,
            fill_opacity=opacity * config.line_opacity,
        )


def create_axis_elements(
    max_values: list[float],
    config: AxisConfig,
) -> list[VElement]:
    """Create all VElements for the value axis.

    Args:
        max_values: List of maximum values, one per frame
        config: Axis configuration (uses defaults if None)

    Returns:
        List of VElements (labels and lines for each tick)
    """
    if config is None:
        config = AxisConfig()

    # Find all tick values needed
    all_ticks = get_all_tick_values(max_values, config.target_tick_count)

    elements = []

    for tick_value in sorted(all_ticks):
        label_keystates = []
        line_keystates = []
        is_zero = tick_value == 0

        for max_val in max_values:
            # Calculate x position
            if max_val > 0:
                x = config.left_x + (tick_value / max_val) * config.width
            else:
                x = config.left_x

            # Determine visibility
            visible = is_tick_visible(tick_value, max_val, config.target_tick_count)
            opacity = 1.0 if visible else 0.0

            # Create states
            label_keystates.append(
                create_tick_label_state(tick_value, x, config.label_y, opacity, config)
            )
            line_keystates.append(
                create_tick_line_state(
                    x, config.line_top_y, config.line_height, opacity, config, is_zero
                )
            )

        # Create VElements
        label_element = VElement().keystates(states=label_keystates)
        line_element = VElement().keystates(states=line_keystates)

        elements.append(label_element)
        elements.append(line_element)

    return elements
