"""VertexLoop class - sequence of vertices forming an open or closed path"""

from __future__ import annotations

import math

from svan2d.core.point2d import Point2D, Points2D


class VertexLoop:
    """A sequence of vertices forming an open or closed loop

    Provides utilities for geometric operations like centroid, area, and bounds.
    Can be subclassed for specific geometric primitives.
    """

    def __init__(self, vertices: Points2D, closed: bool = True):
        """Initialize a vertex loop

        Args:
            vertices: List of (x, y) tuples
            closed: Whether the loop is closed (connects last to first)
        """
        if not vertices:
            raise ValueError("VertexLoop requires at least one vertex")

        # Ensure vertices are Point2D objects
        self._vertices = [
            v if isinstance(v, Point2D) else Point2D(v[0], v[1]) for v in vertices
        ]
        self._closed = closed

    @property
    def vertices(self) -> Points2D:
        """Get vertices as list of tuples"""
        return self._vertices.copy()

    @property
    def closed(self) -> bool:
        """Whether this loop is closed"""
        return self._closed

    def __len__(self) -> int:
        """Number of vertices in the loop"""
        return len(self._vertices)

    def __getitem__(self, index: int) -> Point2D:
        """Get vertex at index"""
        return self._vertices[index]

    def centroid(self) -> Point2D:
        """Calculate the centroid (geometric center) of the vertices

        For closed loops, uses the signed area formula.
        For open loops, uses simple average.
        """
        if not self._vertices:
            return Point2D(0.0, 0.0)

        if not self._closed:
            # Simple average for open loops
            x_sum = sum(v.x for v in self._vertices)
            y_sum = sum(v.y for v in self._vertices)
            n = len(self._vertices)
            return Point2D(x_sum / n, y_sum / n)

        # Signed area formula for closed loops
        area = 0.0
        cx = 0.0
        cy = 0.0

        n = len(self._vertices)
        for i in range(n):
            v1 = self._vertices[i]
            v2 = self._vertices[(i + 1) % n]
            cross = v1.x * v2.y - v2.x * v1.y
            area += cross
            cx += (v1.x + v2.x) * cross
            cy += (v1.y + v2.y) * cross

        if abs(area) < 1e-10:
            # Degenerate case - fall back to simple average
            x_sum = sum(v.x for v in self._vertices)
            y_sum = sum(v.y for v in self._vertices)
            return Point2D(x_sum / n, y_sum / n)

        area *= 0.5
        cx /= 6.0 * area
        cy /= 6.0 * area

        return Point2D(cx, cy)

    def area(self) -> float:
        """Calculate the signed area of the loop

        Positive for counter-clockwise winding, negative for clockwise.
        Returns 0 for open loops.
        """
        if not self._closed or len(self._vertices) < 3:
            return 0.0

        area = 0.0
        n = len(self._vertices)

        for i in range(n):
            v1 = self._vertices[i]
            v2 = self._vertices[(i + 1) % n]
            area += v1.x * v2.y - v2.x * v1.y

        return area * 0.5

    def bounds(self) -> tuple[float, float, float, float]:
        """Calculate bounding box (min_x, min_y, max_x, max_y)"""
        if not self._vertices:
            return (0.0, 0.0, 0.0, 0.0)

        xs = [v.x for v in self._vertices]
        ys = [v.y for v in self._vertices]

        return (min(xs), min(ys), max(xs), max(ys))

    def is_clockwise(self) -> bool:
        """Check if the loop has clockwise winding (negative area)"""
        return self.area() < 0

    def reverse(self) -> VertexLoop:
        """Return a new VertexLoop with reversed vertex order"""
        return VertexLoop(list(reversed(self._vertices)), self._closed)

    def translate(self, dx: float, dy: float) -> VertexLoop:
        """Translate all vertices by (dx, dy). Returns self for chaining."""
        self._vertices = [v + Point2D(dx, dy) for v in self._vertices]
        return self

    def scale(self, sx: float, sy: float | None = None) -> VertexLoop:
        """Scale all vertices by (sx, sy). If sy is None, uses sx for both axes. Returns self for chaining."""
        if sy is None:
            sy = sx
        self._vertices = [Point2D(v.x * sx, v.y * sy) for v in self._vertices]
        return self

    def rotate(self, angle_degrees: float, center: Point2D | None = None) -> VertexLoop:
        """Rotate all vertices by angle_degrees around center (default: origin). Returns self for chaining."""
        rot_center: Point2D = center if center is not None else Point2D(0.0, 0.0)

        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        new_vertices = []
        for v in self._vertices:
            x_rel = v.x - rot_center.x
            y_rel = v.y - rot_center.y
            x_new = x_rel * cos_a - y_rel * sin_a
            y_new = x_rel * sin_a + y_rel * cos_a
            new_vertices.append(Point2D(x_new, y_new) + rot_center)

        self._vertices = new_vertices
        return self
