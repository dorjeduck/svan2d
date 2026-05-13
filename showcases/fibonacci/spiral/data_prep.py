"""Data preparation for the Fibonacci Spiral showcase.

Bridges fibonacci geometry (fibonacci.py) to animation timeline data
ready for VElement creation. Handles scaling, centering, and timing.
"""

import math
from dataclasses import dataclass

from fibonacci import (
    fibonacci_numbers,
    compute_square_layout,
    center_layout,
    compute_spiral_path,
    compute_arc_geometry,
    compute_cumulative_bboxes,
)
from svan2d.core.point2d import Point2D


@dataclass
class SquareData:
    """Per-element timeline data for one Fibonacci square."""

    index: int
    fib_value: int
    center: Point2D
    size: float
    t_start: float
    t_end: float


@dataclass
class SpiralData:
    """Timeline data for the spiral element."""

    path_data: str
    arc_times: list[tuple[float, float]]
    arc_geometry: list[dict]
    cumulative_bboxes: list[tuple[float, float, float, float]]


@dataclass
class FibonacciData:
    """Complete prepared data for the showcase."""

    squares: list[SquareData]
    spiral: SpiralData


def prepare(cfg: dict) -> FibonacciData:
    """Prepare all data for the Fibonacci spiral showcase."""
    n = cfg["fibonacci"]["count"]
    hold_end_ratio = cfg["animation"]["hold_end_ratio"]

    fibs = fibonacci_numbers(n)

    raw_squares, bbox = compute_square_layout(fibs)
    offset_x, offset_y = center_layout(bbox)

    # Animation timing
    arc_times = _compute_arc_times(fibs, hold_end_ratio)

    # Build per-element square data
    squares = []
    for i, sq in enumerate(raw_squares):
        s = sq["size"]
        cx = sq["left"] + s / 2 + offset_x
        cy = sq["top"] + s / 2 + offset_y
        t_start, t_end = arc_times[i]
        squares.append(
            SquareData(
                index=i,
                fib_value=fibs[i],
                center=Point2D(cx, cy),
                size=s,
                t_start=t_start,
                t_end=t_end,
            )
        )

    # Build spiral data (all squares)
    offset_raw = []
    for sq in raw_squares:
        offset_raw.append(
            {
                "size": sq["size"],
                "left": sq["left"] + offset_x,
                "top": sq["top"] + offset_y,
                "right": sq["right"] + offset_x,
                "bottom": sq["bottom"] + offset_y,
            }
        )
    path_data = compute_spiral_path(offset_raw)
    arc_geo = compute_arc_geometry(offset_raw)
    cum_bboxes = compute_cumulative_bboxes(offset_raw)

    spiral = SpiralData(
        path_data=path_data,
        arc_times=arc_times,
        arc_geometry=arc_geo,
        cumulative_bboxes=cum_bboxes,
    )

    return FibonacciData(squares=squares, spiral=spiral)


def _compute_arc_times(
    fibs: list[int], hold_end_ratio: float
) -> list[tuple[float, float]]:
    """Compute (t_start, t_end) for each square/arc segment.

    Timing is proportional to sqrt of arc length (fibonacci number), so the
    spiral draws smoothly via draw_progress and each square fades in
    during the time the spiral passes through it.
    """
    anim_end = 1.0 - hold_end_ratio
    weights = [math.sqrt(f) for f in fibs]
    total_weight = sum(weights)

    times = []
    cumulative = 0.0
    for w in weights:
        t_start = (cumulative / total_weight) * anim_end
        cumulative += w
        t_end = (cumulative / total_weight) * anim_end
        times.append((t_start, t_end))
    return times
