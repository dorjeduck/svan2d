from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator

import math


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


# -------------------------------------------------
# POINT POOL
# -------------------------------------------------
class Point2DPool:
    __slots__ = ("pool", "size", "index")

    def __init__(self, size: int):
        # Preallocate pool with Point2D objects
        self.pool = [Point2D(0.0, 0.0) for _ in range(size)]
        self.size = size
        self.index = 0

    def reset(self):
        """Mark all objects reusable for the next cycle."""
        self.index = 0

    def get(self) -> Point2D:
        """Retrieves and resets the next available Point2D instance."""
        i = self.index

        # Check if we need to grow the pool
        if i >= self.size:
            # Out of space → grow (double)
            old_size = self.size
            new_size = old_size * 2

            # Append new Point2D instances
            self.pool.extend(Point2D(0.0, 0.0) for _ in range(old_size))
            self.size = new_size

        # Increment index and retrieve the point
        self.index = i + 1
        point = self.pool[i]

        point.x = 0.0
        point.y = 0.0

        return point


# ❗ Private global pool
_POINT_POOL = Point2DPool(4096)


def new_point2d(x: float, y: float) -> Point2D:
    """Fast pooled point creation."""
    p = _POINT_POOL.get()
    p.x = x
    p.y = y
    return p


def _reset_point2d_pool() -> None:
    """Internal — called once per frame by the animation loop."""
    _POINT_POOL.reset()


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation"""
    return a + (b - a) * t
