"""Data preparation for 100m Sprint Race Replay.

Embeds split-time data for top 3 finishers from 5 Olympic finals (2008–2024)
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
    reaction_time: float
    splits: list[float]  # Cumulative times at 10m, 20m, ..., 100m
    final_time: float


@dataclass(frozen=True)
class RaceData:
    """Data for a single Olympic 100m final."""

    year: int
    city: str
    runners: list[RunnerSplitData]  # Top 3 finishers


def get_all_races() -> list[RaceData]:
    """Return embedded split data for 5 Olympic 100m finals."""
    return [
        # 2008 Beijing
        RaceData(
            year=2008,
            city="Beijing",
            runners=[
                RunnerSplitData(
                    "Bolt", "JAM", 0.165,
                    [1.85, 2.87, 3.78, 4.65, 5.50, 6.32, 7.14, 7.96, 8.79, 9.69],
                    9.69,
                ),
                RunnerSplitData(
                    "Thompson", "TRI", 0.133,
                    [1.84, 2.89, 3.82, 4.71, 5.58, 6.43, 7.28, 8.11, 8.93, 9.89],
                    9.89,
                ),
                RunnerSplitData(
                    "Dix", "USA", 0.133,
                    [1.83, 2.88, 3.80, 4.69, 5.56, 6.42, 7.28, 8.13, 8.98, 9.91],
                    9.91,
                ),
            ],
        ),
        # 2012 London
        RaceData(
            year=2012,
            city="London",
            runners=[
                RunnerSplitData(
                    "Bolt", "JAM", 0.165,
                    [1.89, 2.88, 3.78, 4.64, 5.47, 6.29, 7.10, 7.92, 8.75, 9.63],
                    9.63,
                ),
                RunnerSplitData(
                    "Blake", "JAM", 0.179,
                    [1.85, 2.86, 3.77, 4.64, 5.49, 6.32, 7.14, 7.96, 8.80, 9.75],
                    9.75,
                ),
                RunnerSplitData(
                    "Gatlin", "USA", 0.178,
                    [1.83, 2.85, 3.76, 4.64, 5.51, 6.36, 7.21, 8.04, 8.87, 9.79],
                    9.79,
                ),
            ],
        ),
        # 2016 Rio
        RaceData(
            year=2016,
            city="Rio",
            runners=[
                RunnerSplitData(
                    "Bolt", "JAM", 0.155,
                    [1.86, 2.87, 3.78, 4.65, 5.49, 6.32, 7.14, 7.96, 8.79, 9.81],
                    9.81,
                ),
                RunnerSplitData(
                    "Gatlin", "USA", 0.152,
                    [1.82, 2.84, 3.76, 4.65, 5.52, 6.38, 7.22, 8.06, 8.90, 9.89],
                    9.89,
                ),
                RunnerSplitData(
                    "De Grasse", "CAN", 0.141,
                    [1.82, 2.85, 3.78, 4.67, 5.55, 6.41, 7.25, 8.09, 8.93, 9.91],
                    9.91,
                ),
            ],
        ),
        # 2020 Tokyo (held 2021)
        RaceData(
            year=2020,
            city="Tokyo",
            runners=[
                RunnerSplitData(
                    "Jacobs", "ITA", 0.161,
                    [1.85, 2.88, 3.80, 4.67, 5.53, 6.37, 7.19, 8.01, 8.84, 9.80],
                    9.80,
                ),
                RunnerSplitData(
                    "Kerley", "USA", 0.128,
                    [1.80, 2.85, 3.78, 4.68, 5.56, 6.42, 7.27, 8.10, 8.93, 9.84],
                    9.84,
                ),
                RunnerSplitData(
                    "De Grasse", "CAN", 0.164,
                    [1.86, 2.89, 3.81, 4.69, 5.55, 6.40, 7.23, 8.06, 8.90, 9.89],
                    9.89,
                ),
            ],
        ),
        # 2024 Paris
        RaceData(
            year=2024,
            city="Paris",
            runners=[
                RunnerSplitData(
                    "Lyles", "USA", 0.178,
                    [1.87, 2.89, 3.80, 4.67, 5.52, 6.35, 7.18, 8.00, 8.83, 9.79],
                    9.79,
                ),
                RunnerSplitData(
                    "Thompson", "JAM", 0.108,
                    [1.77, 2.80, 3.74, 4.64, 5.52, 6.39, 7.23, 8.07, 8.91, 9.79],
                    9.79,
                ),
                RunnerSplitData(
                    "Kerley", "USA", 0.180,
                    [1.88, 2.91, 3.82, 4.69, 5.55, 6.39, 7.22, 8.05, 8.88, 9.81],
                    9.81,
                ),
            ],
        ),
    ]


def get_max_race_time() -> float:
    """Return the slowest final time across all races (for timeline normalization)."""
    return max(
        runner.final_time
        for race in get_all_races()
        for runner in race.runners
    )


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
