"""Spline interpolation utilities."""

from __future__ import annotations

from .point2d import Point2D


def catmull_rom_2d(
    p0: Point2D,
    p1: Point2D,
    p2: Point2D,
    p3: Point2D,
    t: float,
) -> Point2D:
    """Catmull-Rom interpolation between p1 and p2 at parameter t.

    Args:
        p0, p1, p2, p3: Four control points.
        t: Parameter in [0, 1] interpolating between p1 and p2.

    Returns:
        Interpolated Point2D.
    """
    t2 = t * t
    t3 = t2 * t
    x = 0.5 * (
        2 * p1.x
        + (-p0.x + p2.x) * t
        + (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2
        + (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3
    )
    y = 0.5 * (
        2 * p1.y
        + (-p0.y + p2.y) * t
        + (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2
        + (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3
    )
    return Point2D(x, y)


def densify_catmull_rom(
    points: list[Point2D],
    substeps: int = 20,
) -> list[Point2D]:
    """Densify a polyline using Catmull-Rom spline interpolation.

    Inserts *substeps* interpolated points between each consecutive pair of
    input points. Boundary control points are clamped (repeated endpoints).

    Args:
        points:   Original sparse points.
        substeps: Number of sub-steps between each pair of points.

    Returns:
        Densified list of Point2D (approximately len(points) * substeps points).
    """
    n = len(points)
    result = []
    for i in range(n - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(n - 1, i + 2)]
        for s in range(substeps):
            result.append(catmull_rom_2d(p0, p1, p2, p3, s / substeps))
    return result
