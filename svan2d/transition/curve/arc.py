"""Circular arc path interpolation."""

import math
from collections.abc import Callable

from svan2d.core.point2d import Point2D


def _make_arc_path(
    radius: float | None,
    clockwise: bool,
) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Create an arc path function with the given direction.

    Args:
        radius: Arc radius. If None, uses distance between points (semicircle).
        clockwise: If True, arc curves right; if False, curves left.
    """
    # The center calculation flag is inverted relative to the visual direction
    center_clockwise = not clockwise

    def arc_path(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        distance = p1.distance_to(p2)
        if distance == 0:
            return p1

        r = radius if radius is not None else distance
        if r < distance / 2:
            r = distance / 2

        center, start_angle, end_angle = _calculate_arc_center(
            p1, p2, r, clockwise=center_clockwise
        )

        angle_diff = end_angle - start_angle
        if angle_diff < 0:
            angle_diff += 2 * math.pi

        angle = start_angle + angle_diff * t
        return Point2D(
            center.x + r * math.cos(angle),
            center.y + r * math.sin(angle),
        )

    return arc_path


def arc(radius: float | None = None) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Create a circular arc path function (counterclockwise by default).

    Args:
        radius: Arc radius. If None, uses distance between points (semicircle).
    """
    return _make_arc_path(radius, clockwise=False)


def arc_counterclockwise(
    radius: float | None = None,
) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Create a counterclockwise circular arc path function.

    The arc curves to the left when moving from p1 to p2.

    Args:
        radius: Arc radius. If None, uses distance between points (semicircle).
    """
    return _make_arc_path(radius, clockwise=False)


def arc_clockwise(
    radius: float | None = None,
) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Create a clockwise circular arc path function.

    The arc curves to the right when moving from p1 to p2.

    Args:
        radius: Arc radius. If None, uses distance between points (semicircle).
    """
    return _make_arc_path(radius, clockwise=True)


def _calculate_arc_center(
    p1: Point2D, p2: Point2D, radius: float, clockwise: bool
) -> tuple[Point2D, float, float]:
    """Calculate center and angles for circular arc

    Args:
        p1: Start point
        p2: End point
        radius: Arc radius
        clockwise: Direction of arc

    Returns:
        Tuple of (center, start_angle, end_angle)
    """
    # Distance between points
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    distance = math.sqrt(dx * dx + dy * dy)

    # Handle edge cases
    if distance == 0:
        # Points are the same
        return p1, 0.0, 0.0

    if distance > 2 * radius:
        # Defensive: callers clamp radius >= distance/2, so this shouldn't be reached
        return Point2D((p1.x + p2.x) / 2, (p1.y + p2.y) / 2), 0.0, 0.0

    # Midpoint between p1 and p2
    mid_x = (p1.x + p2.x) / 2
    mid_y = (p1.y + p2.y) / 2

    # Perpendicular distance from midpoint to center
    h = math.sqrt(radius * radius - (distance / 2) ** 2)

    # Perpendicular direction (normalized)
    perp_x = -dy / distance
    perp_y = dx / distance

    # Flip direction for clockwise
    if clockwise:
        perp_x = -perp_x
        perp_y = -perp_y

    # Center of arc
    center_x = mid_x + h * perp_x
    center_y = mid_y + h * perp_y
    center = Point2D(center_x, center_y)

    # Calculate start and end angles
    start_angle = math.atan2(p1.y - center_y, p1.x - center_x)
    end_angle = math.atan2(p2.y - center_y, p2.x - center_x)

    return center, start_angle, end_angle
