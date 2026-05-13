"""Year label element for discovery timeline animation."""

from data_prep import TimelineData
from elements import CELL_SIZE, GAP, ROWS

from svan2d import Color, Point2D, TextState, VElement


def create_year_element(
    data: TimelineData,
    font_family: str,
    font_size: float,
    font_weight: str,
    fill_color: Color,
    fill_opacity: float,
) -> VElement:
    """Create a large background year label that updates as elements appear."""
    step = CELL_SIZE + GAP
    table_h = ROWS * step - GAP
    top_y = -table_h / 2
    pos = Point2D(0, top_y)

    year_states: list[TextState] = []
    seen_times: set[float] = set()

    for cell in data.cells:
        if cell.t_start in seen_times:
            continue
        seen_times.add(cell.t_start)

        year = cell.element.discovery_year
        label = f"{abs(year)} BCE" if year < 0 else str(year)

        year_states.append(
            TextState(
                text=label,
                pos=pos,
                font_size=font_size,
                font_family=font_family,
                font_weight=font_weight,
                fill_color=fill_color,
                fill_opacity=fill_opacity,
            )
        )

    return VElement().keystates(states=year_states)
