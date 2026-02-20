"""Year display element for Gapminder bubble chart."""

from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement.velement import VElement


def create_year_element(
    country_data: dict,
    layout: dict,
    font_family: str = "Arial",
    font_size: int = 80,
    font_weight: str = "bold",
    fill_color: Color = Color("#000033"),
    fill_opacity: float = 0.08,
    offset_right: float = 30,
    offset_bottom: float = 20,
) -> VElement:
    """Create the year display element in the lower right of the plot area.

    Args:
        country_data: Dictionary mapping country names to data points
        layout: Layout dictionary with plot bounds
        font_family: Font family for year text
        font_size: Font size for year text
        font_weight: Font weight for year text
        fill_color: Color for year text
        fill_opacity: Opacity for year text
        offset_right: Distance from right edge of plot
        offset_bottom: Distance from bottom edge of plot

    Returns:
        VElement with year keystates
    """
    first_country_data = next(iter(country_data.values()))

    y_pos = layout["plot_bottom"] - offset_bottom
    x_pos = layout["plot_right"] - offset_right

    year_keystates = [
        TextState(
            text=str(int(point.year)),
            pos=Point2D(x_pos, y_pos),
            font_family=font_family,
            font_size=font_size,
            font_weight=font_weight,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            text_anchor="end",
            dominant_baseline="alphabetic",
            z_index=-1.0,
        )
        for point in first_country_data
    ]

    return VElement().keystates(states=year_keystates)
