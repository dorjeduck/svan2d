"""Bezier curve path interpolation"""

import math
from typing import List, Callable
from svan2d.core.point2d import Point2D


def bezier(control_points: List[Point2D]) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Create a bezier curve path function with given control points

    Supports quadratic (1 control point), cubic (2 control points),
    or higher-order bezier curves (3+ control points).

    Args:
        control_points: List of intermediate control points (absolute coordinates)
            - 1 point: quadratic bezier (p1 → cp → p2)
            - 2 points: cubic bezier (p1 → cp1 → cp2 → p2)
            - 3+ points: higher-order bezier curves

    Returns:
        Path function that interpolates along the bezier curve

    Example:
        >>> # Cubic bezier with curve bulging upward
        >>> path_func = bezier([Point2D(50, 200), Point2D(150, 200)])
        >>> path_func(Point2D(0, 0), Point2D(200, 0), 0.5)
        Point2D(100.0, 150.0)  # Point on curve at t=0.5
    """
    if not control_points:
        raise ValueError("bezier() requires at least one control point")

    if not all(isinstance(cp, Point2D) for cp in control_points):
        raise TypeError("All control points must be Point2D objects")

    def bezier_path(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        """Interpolate along bezier curve

        Args:
            p1: Start point
            p2: End point
            t: Interpolation parameter (0.0 to 1.0, already eased)

        Returns:
            Point on bezier curve at parameter t
        """
        # Build full point list: [p1, cp1, cp2, ..., p2]
        pts = [p1] + control_points + [p2]
        n = len(pts) - 1

        # General bezier formula using binomial coefficients
        x = sum(
            math.comb(n, i) * (1 - t) ** (n - i) * t**i * pts[i].x
            for i in range(n + 1)
        )
        y = sum(
            math.comb(n, i) * (1 - t) ** (n - i) * t**i * pts[i].y
            for i in range(n + 1)
        )

        return Point2D(x, y)

    return bezier_path


def bezier_quadratic(control: Point2D) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Convenience function for quadratic bezier with single control point

    Creates a quadratic bezier curve: p1 → control → p2

    Args:
        control: Single control point (absolute coordinates)

    Returns:
        Path function for quadratic bezier curve

    Example:
        >>> path_func = bezier_quadratic(Point2D(100, 200))
        >>> path_func(Point2D(0, 0), Point2D(200, 0), 0.5)
    """
    return bezier([control])


def bezier_cubic(control1: Point2D, control2: Point2D) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Convenience function for cubic bezier with two control points

    Creates a cubic bezier curve: p1 → control1 → control2 → p2

    Args:
        control1: First control point (absolute coordinates)
        control2: Second control point (absolute coordinates)

    Returns:
        Path function for cubic bezier curve

    Example:
        >>> path_func = bezier_cubic(Point2D(50, 200), Point2D(150, 200))
        >>> path_func(Point2D(0, 0), Point2D(200, 0), 0.5)
    """
    return bezier([control1, control2])
