"""Prepare data for scatter_to_grid timeline-buildup animation."""

from bisect import bisect_left
from dataclasses import dataclass

from elements import PADDING, ELEMENTS, ElementData, grid_position, table_size
from svan2d.core.point2d import Point2D


@dataclass(frozen=True)
class CellData:
    element: ElementData
    timeline_pos: Point2D
    grid_pos: Point2D
    t_appear: float
    t_appear_end: float
    t_fly_end: float


@dataclass(frozen=True)
class TickData:
    year: int
    x_pos: float
    t_appear: float


@dataclass(frozen=True)
class AppData:
    cells: list[CellData]
    ticks: list[TickData]
    axis_x_start: float
    axis_x_end: float
    axis_y: float
    tl_cell_size: float
    tl_cell_gap: float


def prepare(cfg: dict) -> AppData:
    """Sort elements by discovery year and compute timeline/grid positions."""
    tlcfg = cfg["timeline"]
    acfg = cfg["animation"]

    buildup_end = acfg["buildup_end"]
    appear_dur = acfg["appear_duration"]
    fly_end = acfg["fly_end"]
    stagger = acfg["fly_stagger_per_period"]

    w, _ = table_size()

    # Axis spans most of the scene width
    axis_x_start = -(w / 2 - PADDING)
    axis_x_end = w / 2 - PADDING
    axis_y = 0.0
    axis_span = axis_x_end - axis_x_start

    sorted_elements = sorted(ELEMENTS, key=lambda e: e.discovery_year)
    n = len(sorted_elements)

    # Derive timeline cell size and gap from spacing
    spacing = axis_span / max(n - 1, 1)
    tl_cell_gap = spacing * 0.15
    tl_cell_size = spacing - tl_cell_gap

    # Distribute t_appear evenly across [0, buildup_end - appear_dur]
    spread = max(buildup_end - appear_dur, 0.01)

    # Timeline y: above the axis
    tl_y = axis_y - tl_cell_size / 2 - tl_cell_gap

    cells: list[CellData] = []
    for i, elem in enumerate(sorted_elements):
        tl_x = axis_x_start + i * spacing
        t_appear = (i / max(n - 1, 1)) * spread
        t_appear_end = min(t_appear + appear_dur, buildup_end)

        gpos = grid_position(elem)

        # Stagger fly arrival by period (row 1 arrives first)
        period = elem.period
        t_fly = min(fly_end + (period - 1) * stagger, 1.0)

        cells.append(
            CellData(
                element=elem,
                timeline_pos=Point2D(tl_x, tl_y),
                grid_pos=gpos,
                t_appear=t_appear,
                t_appear_end=t_appear_end,
                t_fly_end=t_fly,
            )
        )

    # Tick data: map tick_years to x positions via sorted element years
    years = [elem.discovery_year for elem in sorted_elements]
    x_positions = [axis_x_start + i * spacing for i in range(n)]

    ticks: list[TickData] = []
    for ty in tlcfg["tick_years"]:
        idx = bisect_left(years, ty)
        if idx == 0:
            tick_x = x_positions[0]
        elif idx >= n:
            tick_x = x_positions[-1]
        else:
            y_lo, y_hi = years[idx - 1], years[idx]
            x_lo, x_hi = x_positions[idx - 1], x_positions[idx]
            if y_hi == y_lo:
                tick_x = x_lo
            else:
                frac = (ty - y_lo) / (y_hi - y_lo)
                tick_x = x_lo + frac * (x_hi - x_lo)

        # Tick appears when axis draw_progress reaches this x
        tick_t = buildup_end * (tick_x - axis_x_start) / axis_span
        ticks.append(TickData(year=ty, x_pos=tick_x, t_appear=max(tick_t, 0.0)))

    return AppData(
        cells=cells,
        ticks=ticks,
        axis_x_start=axis_x_start,
        axis_x_end=axis_x_end,
        axis_y=axis_y,
        tl_cell_size=tl_cell_size,
        tl_cell_gap=tl_cell_gap,
    )
