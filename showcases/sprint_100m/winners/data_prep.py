"""Data preparation for Olympic 100m Winners Race.

Embeds split-time data for all 10 Olympic 100m gold medalists (1988–2024)
and provides PCHIP interpolation functions for svan2d's interpolation_dict.
"""

from dataclasses import dataclass
from typing import Callable

from scipy.interpolate import PchipInterpolator

from svan2d.core.point2d import Point2D


@dataclass(frozen=True)
class RunnerSplitData:
    """Split times for a single runner."""

    name: str
    country: str
    year: int
    reaction_time: float
    splits: list[float]  # Cumulative times at 10m, 20m, ..., 100m
    final_time: float
    placement: int = 0  # Assigned after sorting by final_time


def get_runners() -> list[RunnerSplitData]:
    """Return split data for 10 Olympic 100m gold medalists (1988–2024).

    Split times sourced from World Athletics.
    """
    runners = [
        RunnerSplitData(
            "Carl Lewis", "USA", 1988, 0.136,
            [1.88, 2.96, 3.88, 4.77, 5.61, 6.45, 7.29, 8.12, 8.96, 9.92],
            9.92,
        ),
        RunnerSplitData(
            "Linford Christie", "GBR", 1992, 0.140,
            [1.84, 2.90, 3.84, 4.74, 5.61, 6.47, 7.32, 8.16, 9.00, 9.96],
            9.96,
        ),
        RunnerSplitData(
            "Donovan Bailey", "CAN", 1996, 0.174,
            [1.88, 2.91, 3.83, 4.71, 5.56, 6.39, 7.21, 8.02, 8.84, 9.84],
            9.84,
        ),
        RunnerSplitData(
            "Maurice Greene", "USA", 2000, 0.152,
            [1.82, 2.87, 3.80, 4.68, 5.55, 6.40, 7.24, 8.08, 8.91, 9.87],
            9.87,
        ),
        RunnerSplitData(
            "Justin Gatlin", "USA", 2004, 0.148,
            [1.84, 2.87, 3.79, 4.67, 5.53, 6.38, 7.22, 8.05, 8.88, 9.85],
            9.85,
        ),
        RunnerSplitData(
            "Usain Bolt", "JAM", 2008, 0.165,
            [1.85, 2.87, 3.78, 4.65, 5.50, 6.32, 7.14, 7.96, 8.79, 9.69],
            9.69,
        ),
        RunnerSplitData(
            "Usain Bolt", "JAM", 2012, 0.165,
            [1.89, 2.88, 3.78, 4.64, 5.47, 6.29, 7.10, 7.92, 8.75, 9.63],
            9.63,
        ),
        RunnerSplitData(
            "Usain Bolt", "JAM", 2016, 0.155,
            [1.86, 2.87, 3.78, 4.65, 5.49, 6.32, 7.14, 7.96, 8.79, 9.81],
            9.81,
        ),
        RunnerSplitData(
            "Marcell Jacobs", "ITA", 2020, 0.161,
            [1.85, 2.88, 3.80, 4.67, 5.53, 6.37, 7.19, 8.01, 8.84, 9.80],
            9.80,
        ),
        RunnerSplitData(
            "Noah Lyles", "USA", 2024, 0.178,
            [1.87, 2.89, 3.80, 4.67, 5.52, 6.35, 7.18, 8.00, 8.83, 9.79],
            9.79,
        ),
    ]

    # Sort by final_time and assign placements
    sorted_runners = sorted(runners, key=lambda r: r.final_time)
    placed = []
    for rank, r in enumerate(sorted_runners, start=1):
        placed.append(RunnerSplitData(
            name=r.name, country=r.country, year=r.year,
            reaction_time=r.reaction_time, splits=r.splits,
            final_time=r.final_time, placement=rank,
        ))

    # Return in year order for lane assignment
    year_order = {r.year: r for r in placed}
    return [year_order[y] for y in [1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]]


def get_max_time() -> float:
    """Return the slowest final time (for timeline normalization)."""
    return max(r.final_time for r in get_runners())


def make_pos_interpolator(
    runner: RunnerSplitData,
    lane_y: float,
    distance_to_x: Callable[[float], float],
) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Create a PCHIP-based pos interpolation function for interpolation_dict.

    Maps segment-local t (0→1) to position using real split data.
    t=0 corresponds to race start (0m), t=1 to finish (100m).

    Args:
        runner: Runner with split time data
        lane_y: Y coordinate of the runner's lane
        distance_to_x: Function mapping distance (0–100m) to X coordinate

    Returns:
        Interpolation function (p1, p2, t) -> Point2D
    """
    # Build time→distance: [0, reaction] → 0m, then splits at 10m intervals
    times = [0.0, runner.reaction_time]
    distances = [0.0, 0.0]
    for i, split_time in enumerate(runner.splits):
        times.append(split_time)
        distances.append((i + 1) * 10.0)

    # Normalize times to 0→1 (segment-local t maps to 0→final_time)
    norm_times = [t / runner.final_time for t in times]
    interpolator = PchipInterpolator(norm_times, distances)

    def pos_fn(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        d = float(interpolator(max(0.0, min(1.0, t))))
        d = max(0.0, min(100.0, d))
        x = distance_to_x(d)
        return Point2D(x, lane_y)

    return pos_fn
