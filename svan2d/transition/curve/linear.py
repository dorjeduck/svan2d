"""Linear path interpolation"""

from svan2d.core.point2d import Point2D


def linear(p1: Point2D, p2: Point2D, t: float) -> Point2D:
    """Linear interpolation between two points (default path function)

    Args:
        p1: Start point
        p2: End point
        t: Interpolation parameter (0.0 to 1.0, already eased)

    Returns:
        Point interpolated linearly between p1 and p2

    Example:
        linear(Point2D(0, 0), Point2D(100, 100), 0.5)
        Point2D(50.0, 50.0)
    """
    return Point2D(x=p1.x + (p2.x - p1.x) * t, y=p1.y + (p2.y - p1.y) * t)
