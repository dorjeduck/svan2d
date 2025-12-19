"""Circular arc path interpolation"""

import math
from typing import Optional, Callable
from svan2d.core.point2d import Point2D


def arc(radius: Optional[float] = None) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Create a circular arc path function (counterclockwise by default)

    Args:
        radius: Arc radius. If None, uses distance between points (semicircle)

    Returns:
        Path function that interpolates along circular arc

    Example:
        path_func = arc(150)
        path_func(Point2D(0, 0), Point2D(200, 0), 0.5)
    """
    return arc_counterclockwise(radius)


def arc_counterclockwise(
    radius: Optional[float] = None,
) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Create a counterclockwise circular arc path function

    The arc curves to the left when moving from p1 to p2.

    Args:
        radius: Arc radius. If None, uses distance between points (semicircle)

    Returns:
        Path function that interpolates along counterclockwise arc

    Example:
        path_func = arc_counterclockwise(150)
        path_func(Point2D(0, 0), Point2D(200, 0), 0.5)
    """

    def arc_ccw_path(p1: Point2D, p2: Point2D, t: float) -> Point2D:

        distance = p1.distance_to(p2)

        if distance == 0:
            return p1

        # Use provided radius or default to distance (semicircle)
        r = radius if radius is not None else distance

        # If radius is too small, clamp to minimum (semicircle)
        if r < distance / 2:
            r = distance / 2

        # Calculate arc (use clockwise=True to get center on correct side)
        center, start_angle, end_angle = _calculate_arc_center(
            p1, p2, r, clockwise=True
        )

        # Normalize angle difference to take shorter arc
        angle_diff = end_angle - start_angle
        if angle_diff < 0:
            angle_diff += 2 * math.pi

        # Interpolate angle
        angle = start_angle + angle_diff * t

        # Calculate point on arc
        x = center.x + r * math.cos(angle)
        y = center.y + r * math.sin(angle)

        return Point2D(x, y)

    return arc_ccw_path


def arc_clockwise(
    radius: Optional[float] = None,
) -> Callable[[Point2D, Point2D, float], Point2D]:
    """Create a clockwise circular arc path function

    The arc curves to the right when moving from p1 to p2.

    Args:
        radius: Arc radius. If None, uses distance between points (semicircle)

    Returns:
        Path function that interpolates along clockwise arc

    Example:
        path_func = arc_clockwise(150)
        path_func(Point2D(0, 0), Point2D(200, 0), 0.5)
    """

    def arc_cw_path(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        # Calculate distance
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance == 0:
            return p1

        # Use provided radius or default to distance (semicircle)
        r = radius if radius is not None else distance

        # If radius is too small, clamp to minimum (semicircle)
        if r < distance / 2:
            r = distance / 2

        # Calculate arc (use clockwise=False to get center on correct side)
        center, start_angle, end_angle = _calculate_arc_center(
            p1, p2, r, clockwise=False
        )

        # Normalize angle difference to take shorter arc
        angle_diff = end_angle - start_angle
        if angle_diff < 0:
            angle_diff += 2 * math.pi

        # Interpolate angle
        angle = start_angle + angle_diff * t

        # Calculate point on arc
        x = center.x + r * math.cos(angle)
        y = center.y + r * math.sin(angle)

        return Point2D(x, y)

    return arc_cw_path


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
        # Radius too small - fall back to straight line
        # (caller should handle this)
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
