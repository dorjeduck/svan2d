"""2D point and point list types with vector operations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterator


@dataclass(slots=True, frozen=True)
class Point2D:
    """
    A single point in 2D space (immutable and memory efficient).
    """

    x: float = 0
    y: float = 0

    def __iter__(self) -> Iterator[float]:
        """Allows direct unpacking: x, y = point"""
        yield self.x
        yield self.y

    def distance_to(self, other: Point2D) -> float:
        """Calculate Euclidean distance to another point using math.hypot."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def center_to(self, other: Point2D):
        return Point2D((self.x + other.x) / 2, (self.y + other.y) / 2)

    def rotation_to(self, other: Point2D):
        return math.degrees(math.atan2(other.y - self.y, other.x - self.x))

    def with_x(self, x):
        return Point2D(x, self.y)

    def with_y(self, y):
        return Point2D(self.x, y)

    # -------------------------------------------------------------
    # IMMUTABLE OPERATORS (Return a NEW object)
    # -------------------------------------------------------------
    def __add__(self, other: Point2D) -> Point2D:
        """Add two points (vector addition)"""
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point2D) -> Point2D:
        """Subtract two points (vector subtraction)"""
        return Point2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Point2D:
        """Multiply point by scalar"""
        return Point2D(self.x * scalar, self.y * scalar)

    def __neg__(self) -> "Point2D":
        """Return a new Point2D with both coordinates negated."""
        return Point2D(-self.x, -self.y)

    def __truediv__(self, scalar: float) -> Point2D:
        """Divide point by scalar"""
        if scalar == 0.0:
            raise ZeroDivisionError("Cannot divide Point2D by zero scalar.")
        return Point2D(self.x / scalar, self.y / scalar)

    def __rmul__(self, scalar: float) -> Point2D:
        """Reverse multiply point by scalar (e.g., 2.0 * point)"""
        return self * scalar

    def lerp(self, p2: Point2D, t: float) -> Point2D:
        """Linear interpolation between two points (returns a NEW point)"""
        return Point2D(x=_lerp(self.x, p2.x, t), y=_lerp(self.y, p2.y, t))


Points2D = list[Point2D]


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation"""
    return a + (b - a) * t
