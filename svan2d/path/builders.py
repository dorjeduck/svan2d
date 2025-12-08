from svan2d.core.point2d import Point2D
from .commands import (
    MoveTo,
    LineTo,
    QuadraticBezier,
    CubicBezier,
    ClosePath,
)
from .svg_path import SVGPath


# ============================================================================
# Helper functions for creating common paths
# ============================================================================


def line(start: Point2D, end: Point2D) -> SVGPath:
    """Create a straight line path"""
    return SVGPath([MoveTo(start), LineTo(end)])


def quadratic_curve(p1: Point2D, p2: Point2D, p3: Point2D) -> SVGPath:
    """Create a quadratic Bezier curve path"""
    return SVGPath([MoveTo(p1), QuadraticBezier(p2, p3)])


def cubic_curve(
    p1: Point2D,
    p2: Point2D,
    p3: Point2D,
    p4: Point2D,
) -> SVGPath:
    """Create a cubic Bezier curve path"""
    return SVGPath([MoveTo(p1), CubicBezier(p2, p3, p4)])


def rectangle(pos: Point2D, width: float, height: float) -> SVGPath:
    """Create a rectangle path"""
    return SVGPath(
        [
            MoveTo(pos),
            LineTo(Point2D(pos.x + width, pos.y)),
            LineTo(Point2D(pos.x + width, pos.y + height)),
            LineTo(Point2D(pos.x, pos.y + height)),
            ClosePath(),
        ]
    )


def circle_as_beziers(center: Point2D, radius: float) -> SVGPath:
    """Create a circle path using cubic Bezier curves

    Uses the magic constant 0.551915024494 for circle approximation
    """
    k = 0.551915024494  # Magic constant for circle with cubic beziers

    return SVGPath(
        [
            MoveTo(Point2D(center.x, center.y - radius)),  # Top
            CubicBezier(
                Point2D(center.x + k * radius, center.y - radius),
                Point2D(center.x + radius, center.y - k * radius),
                Point2D(center.x + radius, center.y),
            ),  # Right
            CubicBezier(
                Point2D(center.x + radius, center.y + k * radius),
                Point2D(center.x + k * radius, center.y + radius),
                Point2D(center.x, center.y + radius),
            ),  # Bottom
            CubicBezier(
                Point2D(center.x - k * radius, center.y + radius),
                Point2D(center.x - radius, center.y + k * radius),
                Point2D(center.x - radius, center.y),
            ),  # Left
            CubicBezier(
                Point2D(center.x - radius, center.y - k * radius),
                Point2D(center.x - k * radius, center.y - radius),
                Point2D(center.x, center.y - radius),
            ),  # Back to top
            ClosePath(),
        ]
    )
