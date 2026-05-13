"""Prepare timeline data for discovery_timeline animation."""

from dataclasses import dataclass

from elements import ELEMENTS, ElementData, grid_position
from svan2d import Point2D


@dataclass(frozen=True)
class CellData:
    element: ElementData
    pos: Point2D
    t_start: float
    t_end: float


@dataclass(frozen=True)
class TimelineData:
    cells: list[CellData]


def prepare(cfg: dict) -> TimelineData:
    """Sort elements by discovery year and assign staggered appear times."""
    acfg = cfg["animation"]

    sorted_elements = sorted(ELEMENTS, key=lambda e: e.discovery_year)

    hold_end = acfg["hold_end_ratio"]
    appear_dur = acfg["appear_duration"]
    active_range = 1.0 - hold_end

    n = len(sorted_elements)
    # Distribute start times evenly across [0, active_range - appear_dur]
    spread = max(active_range - appear_dur, 0.01)

    cells: list[CellData] = []
    for i, elem in enumerate(sorted_elements):
        pos = grid_position(elem)
        t_start = (i / max(n - 1, 1)) * spread
        t_end = min(t_start + appear_dur, 1.0)
        cells.append(CellData(element=elem, pos=pos, t_start=t_start, t_end=t_end))

    return TimelineData(cells=cells)
