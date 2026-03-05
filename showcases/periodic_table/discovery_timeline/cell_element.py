"""Cell element creation for discovery_timeline animation."""

from dataclasses import replace

from data_prep import CellData, TimelineData
from elements import CATEGORY_COLORS

from svan2d.component.state.square import SquareState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement.velement import VElement


def _create_cell(
    cell: CellData,
    cell_size: float,
    fill_opacity: float,
    stroke_color: Color,
    stroke_width: float,
    stroke_opacity: float,
    font_family: str,
    font_weight: str,
    symbol_font_size: float,
    number_font_size: float,
    number_opacity: float,
    number_offset: float,
    label_color: Color,
) -> list[VElement]:
    """Create 3 VElements for one cell: square, symbol, atomic number."""
    cat_color = Color(CATEGORY_COLORS[cell.element.category])

    # Square
    base_square = SquareState(
        size=cell_size,
        pos=cell.pos,
        fill_color=cat_color,
        fill_opacity=fill_opacity,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        stroke_opacity=stroke_opacity,
        scale=0.0,
        opacity=0.0,
    )
    visible_square = replace(base_square, scale=1.0, opacity=1.0)

    sq_vel = (
        VElement()
        .keystate(base_square, at=cell.t_start)
        .transition(easing_dict={"scale": easing.out_back, "opacity": easing.out_quad})
        .keystate(visible_square, at=cell.t_end)
    )
    if cell.t_end < 1.0:
        sq_vel = sq_vel.keystate(visible_square, at=1.0)

    # Symbol
    base_symbol = TextState(
        text=cell.element.symbol,
        pos=cell.pos,
        font_size=symbol_font_size,
        font_family=font_family,
        font_weight=font_weight,
        fill_color=label_color,
        scale=0.0,
        opacity=0.0,
        z_index=1.0,
    )
    visible_symbol = replace(base_symbol, scale=1.0, opacity=1.0)

    sym_vel = (
        VElement()
        .keystate(base_symbol, at=cell.t_start)
        .transition(easing_dict={"scale": easing.out_back, "opacity": easing.out_quad})
        .keystate(visible_symbol, at=cell.t_end)
    )
    if cell.t_end < 1.0:
        sym_vel = sym_vel.keystate(visible_symbol, at=1.0)

    # Atomic number
    num_pos = Point2D(
        cell.pos.x + cell_size * number_offset,
        cell.pos.y + cell_size * number_offset,
    )
    base_number = TextState(
        text=str(cell.element.atomic_number),
        pos=num_pos,
        font_size=number_font_size,
        font_family=font_family,
        fill_color=label_color,
        fill_opacity=number_opacity,
        scale=0.0,
        opacity=0.0,
        z_index=1.0,
    )
    visible_number = replace(base_number, scale=1.0, opacity=1.0)

    num_vel = (
        VElement()
        .keystate(base_number, at=cell.t_start)
        .transition(easing_dict={"scale": easing.out_back, "opacity": easing.out_quad})
        .keystate(visible_number, at=cell.t_end)
    )
    if cell.t_end < 1.0:
        num_vel = num_vel.keystate(visible_number, at=1.0)

    return [sq_vel, sym_vel, num_vel]


def create_cell_elements(
    data: TimelineData,
    cell_size: float,
    fill_opacity: float,
    stroke_color: Color,
    stroke_width: float,
    stroke_opacity: float,
    font_family: str,
    font_weight: str,
    symbol_font_size: float,
    number_font_size: float,
    number_opacity: float,
    number_offset: float,
    label_color: Color,
) -> list[VElement]:
    """Create VElements for all cells."""
    result: list[VElement] = []
    for cell in data.cells:
        result.extend(
            _create_cell(
                cell,
                cell_size=cell_size,
                fill_opacity=fill_opacity,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                stroke_opacity=stroke_opacity,
                font_family=font_family,
                font_weight=font_weight,
                symbol_font_size=symbol_font_size,
                number_font_size=number_font_size,
                number_opacity=number_opacity,
                number_offset=number_offset,
                label_color=label_color,
            )
        )
    return result
