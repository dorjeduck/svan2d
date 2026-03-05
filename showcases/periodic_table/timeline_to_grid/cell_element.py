"""Cell element creation for scatter_to_grid timeline-buildup animation."""

from dataclasses import replace

from data_prep import CellData, AppData
from elements import CATEGORY_COLORS

from svan2d.component.state.square import SquareState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.transition.easing import easing2D
from svan2d.velement.velement import VElement


def _create_cell(
    cell: CellData,
    cell_size: float,
    timeline_cell_size: float,
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
    buildup_end: float,
) -> list[VElement]:
    """Create 3 VElements for one cell: square, symbol, atomic number."""
    cat_color = Color(CATEGORY_COLORS[cell.element.category])

    # --- Square (5 keystates) ---
    # KS1: hidden at timeline pos
    sq_hidden = SquareState(
        size=timeline_cell_size,
        pos=cell.timeline_pos,
        fill_color=cat_color,
        fill_opacity=fill_opacity,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        stroke_opacity=stroke_opacity,
        scale=0.0,
        opacity=0.0,
    )
    # KS2: visible at timeline pos (pop in)
    sq_timeline = replace(sq_hidden, scale=1.0, opacity=1.0)
    # KS3: same as KS2 (hold at timeline pos until buildup_end)
    # KS4: at grid pos, full cell_size
    sq_grid = replace(
        sq_timeline,
        size=cell_size,
        pos=cell.grid_pos,
    )
    # KS5: same as KS4 (hold at grid pos)

    sq_vel = (
        VElement()
        .keystate(sq_hidden, at=cell.t_appear)
        .transition(easing_dict={"scale": easing.out_back, "opacity": easing.out_quad})
        .keystate(sq_timeline, at=cell.t_appear_end)
        .keystate(sq_timeline, at=buildup_end)
        .transition(
            easing_dict={
                "pos": easing2D(easing.in_out_cubic, easing.out_cubic),
                "size": easing.in_out_quad,
            },
        )
        .keystate(sq_grid, at=cell.t_fly_end)
        .keystate(sq_grid, at=1.0)
    )

    # Font sizes scale proportionally with cell size
    size_ratio = timeline_cell_size / cell_size
    tl_symbol_fs = symbol_font_size * size_ratio
    tl_number_fs = number_font_size * size_ratio

    # --- Symbol text (5 keystates, same lifecycle as square) ---
    sym_hidden = TextState(
        text=cell.element.symbol,
        pos=cell.timeline_pos,
        font_size=tl_symbol_fs,
        font_family=font_family,
        font_weight=font_weight,
        fill_color=label_color,
        scale=0.0,
        opacity=0.0,
        z_index=1.0,
    )
    sym_timeline = replace(sym_hidden, scale=1.0, opacity=1.0)
    sym_grid = replace(sym_timeline, pos=cell.grid_pos, font_size=symbol_font_size)

    sym_vel = (
        VElement()
        .keystate(sym_hidden, at=cell.t_appear)
        .transition(easing_dict={"scale": easing.out_back, "opacity": easing.out_quad})
        .keystate(sym_timeline, at=cell.t_appear_end)
        .keystate(sym_timeline, at=buildup_end)
        .transition(
            easing_dict={
                "pos": easing2D(easing.in_out_cubic, easing.out_cubic),
                "font_size": easing.in_out_quad,
            },
        )
        .keystate(sym_grid, at=cell.t_fly_end)
        .keystate(sym_grid, at=1.0)
    )

    # --- Atomic number text (5 keystates, same lifecycle as square) ---
    tl_num_pos = Point2D(
        cell.timeline_pos.x + timeline_cell_size * number_offset,
        cell.timeline_pos.y + timeline_cell_size * number_offset,
    )
    grid_num_pos = Point2D(
        cell.grid_pos.x + cell_size * number_offset,
        cell.grid_pos.y + cell_size * number_offset,
    )
    num_hidden = TextState(
        text=str(cell.element.atomic_number),
        pos=tl_num_pos,
        font_size=tl_number_fs,
        font_family=font_family,
        fill_color=label_color,
        fill_opacity=number_opacity,
        scale=0.0,
        opacity=0.0,
        z_index=1.0,
    )
    num_timeline = replace(num_hidden, scale=1.0, opacity=1.0)
    num_grid = replace(num_timeline, pos=grid_num_pos, font_size=number_font_size)

    num_vel = (
        VElement()
        .keystate(num_hidden, at=cell.t_appear)
        .transition(easing_dict={"scale": easing.out_back, "opacity": easing.out_quad})
        .keystate(num_timeline, at=cell.t_appear_end)
        .keystate(num_timeline, at=buildup_end)
        .transition(
            easing_dict={
                "pos": easing2D(easing.in_out_cubic, easing.out_cubic),
                "font_size": easing.in_out_quad,
            },
        )
        .keystate(num_grid, at=cell.t_fly_end)
        .keystate(num_grid, at=1.0)
    )

    return [sq_vel, sym_vel, num_vel]


def create_cell_elements(
    data: AppData,
    cell_size: float,
    timeline_cell_size: float,
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
    buildup_end: float,
) -> list[VElement]:
    """Create VElements for all cells."""
    result: list[VElement] = []
    for cell in data.cells:
        result.extend(
            _create_cell(
                cell,
                cell_size=cell_size,
                timeline_cell_size=timeline_cell_size,
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
                buildup_end=buildup_end,
            )
        )
    return result
