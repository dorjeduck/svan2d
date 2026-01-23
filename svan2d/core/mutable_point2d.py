"""Mutable Point2D with object pooling for performance-critical paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .point2d import Point2D


@dataclass(slots=True)
class MutablePoint2D:
    """Mutable point for internal hot paths (pooled)."""

    x: float = 0.0
    y: float = 0.0

    def to_point2d(self) -> "Point2D":
        from .point2d import Point2D

        return Point2D(self.x, self.y)

    def set(self, x: float, y: float) -> "MutablePoint2D":
        self.x = x
        self.y = y
        return self

    def lerp_from(self, p1: "Point2D", p2: "Point2D", t: float) -> "MutablePoint2D":
        """In-place lerp: sets self to interpolated value."""
        self.x = p1.x + (p2.x - p1.x) * t
        self.y = p1.y + (p2.y - p1.y) * t
        return self


class MutablePoint2DPool:
    """Object pool for MutablePoint2D to reduce allocations."""

    __slots__ = ("_pool", "_size", "_index")

    def __init__(self, initial_size: int = 4096):
        self._pool = [MutablePoint2D() for _ in range(initial_size)]
        self._size = initial_size
        self._index = 0

    def reset(self) -> None:
        """Reset pool index. Call at start of each frame."""
        self._index = 0

    def get(self, x: float = 0.0, y: float = 0.0) -> MutablePoint2D:
        """Get a point from pool with given coordinates."""
        i = self._index
        if i >= self._size:
            # Grow pool by doubling
            self._pool.extend(MutablePoint2D() for _ in range(self._size))
            self._size *= 2

        self._index = i + 1
        p = self._pool[i]
        p.x = x
        p.y = y
        return p

    @property
    def used(self) -> int:
        return self._index

    @property
    def capacity(self) -> int:
        return self._size


# Global pool instance
_pool = MutablePoint2DPool(8192)


def get_pooled_point(x: float = 0.0, y: float = 0.0) -> MutablePoint2D:
    """Get a MutablePoint2D from the global pool."""
    return _pool.get(x, y)


def reset_point_pool() -> None:
    """Reset the global pool. Call once per frame."""
    _pool.reset()


def get_pool_stats() -> tuple[int, int]:
    """Return (used, capacity) for debugging."""
    return _pool.used, _pool.capacity
