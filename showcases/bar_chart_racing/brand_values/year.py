"""Year display element for bar chart race animation."""

from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement.velement import VElement


def create_year_element(
    company_data: dict,
    layout: dict,
    font_family: str = "Inter",
    font_size: int = 64,
    fill_color: Color = Color("#000044"),
    fill_opacity: float = 0.15,
    offset_right: float = 5,
    offset_bottom: float = 20,
) -> VElement:
    """Create the year display element in the lower right corner.

    Args:
        company_data: Dictionary mapping company names to data points
        layout: Layout dictionary with plot bounds
        font_family: Font family for year text
        font_size: Font size for year text
        fill_color: Color for year text
        fill_opacity: Opacity for year text
        offset_right: Distance from right edge
        offset_bottom: Distance from bottom edge

    Returns:
        VElement with year keystates
    """
    first_company_data = next(iter(company_data.values()))

    # With dominant_baseline="alphabetic", pos.y is at text baseline
    # offset_bottom = distance from plot_bottom to baseline
    y_pos = layout["plot_bottom"] - offset_bottom

    year_keystates = [
        TextState(
            text=str(int(point.year)),
            pos=Point2D(layout["plot_right"] - offset_right, y_pos),
            font_family=font_family,
            font_size=font_size,
            font_weight="bold",
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            text_anchor="end",
            dominant_baseline="alphabetic",
        )
        for point in first_company_data
    ]

    return VElement().keystates(states=year_keystates)
