"""Sample bezier curves to evenly-spaced vertices"""

from __future__ import annotations

import math
from typing import List, Tuple

from svan2d.core.point2d import Point2D, Points2D


def sample_quadratic_bezier(
    p0: Point2D, p1: Point2D, p2: Point2D, num_samples: int
) -> Points2D:
    """Sample a quadratic bezier curve at equal t intervals.

    Args:
        p0: Start point
        p1: Control point
        p2: End point
        num_samples: Number of samples (including start, excluding end)

    Returns:
        List of Point2D samples along the curve
    """
    points = []
    for i in range(num_samples):
        t = i / num_samples
        # B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
        mt = 1 - t
        x = mt * mt * p0.x + 2 * mt * t * p1.x + t * t * p2.x
        y = mt * mt * p0.y + 2 * mt * t * p1.y + t * t * p2.y
        points.append(Point2D(x, y))
    return points


def sample_cubic_bezier(
    p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D, num_samples: int
) -> Points2D:
    """Sample a cubic bezier curve at equal t intervals.

    Args:
        p0: Start point
        p1: First control point
        p2: Second control point
        p3: End point
        num_samples: Number of samples (including start, excluding end)

    Returns:
        List of Point2D samples along the curve
    """
    points = []
    for i in range(num_samples):
        t = i / num_samples
        # B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        t2 = t * t
        t3 = t2 * t
        x = mt3 * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t3 * p3.x
        y = mt3 * p0.y + 3 * mt2 * t * p1.y + 3 * mt * t2 * p2.y + t3 * p3.y
        points.append(Point2D(x, y))
    return points


def estimate_quadratic_arc_length(p0: Point2D, p1: Point2D, p2: Point2D, num_segments: int = 20) -> float:
    """Estimate arc length of a quadratic bezier by sampling."""
    length = 0.0
    prev = p0
    for i in range(1, num_segments + 1):
        t = i / num_segments
        mt = 1 - t
        x = mt * mt * p0.x + 2 * mt * t * p1.x + t * t * p2.x
        y = mt * mt * p0.y + 2 * mt * t * p1.y + t * t * p2.y
        curr = Point2D(x, y)
        length += math.sqrt((curr.x - prev.x) ** 2 + (curr.y - prev.y) ** 2)
        prev = curr
    return length


def estimate_cubic_arc_length(p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D, num_segments: int = 20) -> float:
    """Estimate arc length of a cubic bezier by sampling."""
    length = 0.0
    prev = p0
    for i in range(1, num_segments + 1):
        t = i / num_segments
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        t2 = t * t
        t3 = t2 * t
        x = mt3 * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t3 * p3.x
        y = mt3 * p0.y + 3 * mt2 * t * p1.y + 3 * mt * t2 * p2.y + t3 * p3.y
        curr = Point2D(x, y)
        length += math.sqrt((curr.x - prev.x) ** 2 + (curr.y - prev.y) ** 2)
        prev = curr
    return length


def estimate_line_arc_length(p0: Point2D, p1: Point2D) -> float:
    """Calculate arc length of a line segment."""
    return math.sqrt((p1.x - p0.x) ** 2 + (p1.y - p0.y) ** 2)


def sample_quadratic_arc_length(
    p0: Point2D, p1: Point2D, p2: Point2D, num_samples: int
) -> Points2D:
    """Sample a quadratic bezier at equal arc-length intervals.

    Uses adaptive sampling to find t values that produce evenly-spaced points.
    """
    if num_samples <= 1:
        return [p0]

    # Build arc-length lookup table
    table_size = max(100, num_samples * 5)
    arc_lengths = [0.0]
    prev = p0

    for i in range(1, table_size + 1):
        t = i / table_size
        mt = 1 - t
        x = mt * mt * p0.x + 2 * mt * t * p1.x + t * t * p2.x
        y = mt * mt * p0.y + 2 * mt * t * p1.y + t * t * p2.y
        curr = Point2D(x, y)
        arc_lengths.append(arc_lengths[-1] + math.sqrt((curr.x - prev.x) ** 2 + (curr.y - prev.y) ** 2))
        prev = curr

    total_length = arc_lengths[-1]
    if total_length < 1e-10:
        return [p0] * num_samples

    # Sample at equal arc-length intervals
    points = []
    for i in range(num_samples):
        target_length = (i / num_samples) * total_length

        # Binary search for t
        low, high = 0, table_size
        while high - low > 1:
            mid = (low + high) // 2
            if arc_lengths[mid] < target_length:
                low = mid
            else:
                high = mid

        # Linear interpolation between table entries
        if high < len(arc_lengths) and arc_lengths[high] != arc_lengths[low]:
            frac = (target_length - arc_lengths[low]) / (arc_lengths[high] - arc_lengths[low])
            t = (low + frac) / table_size
        else:
            t = low / table_size

        mt = 1 - t
        x = mt * mt * p0.x + 2 * mt * t * p1.x + t * t * p2.x
        y = mt * mt * p0.y + 2 * mt * t * p1.y + t * t * p2.y
        points.append(Point2D(x, y))

    return points


def sample_cubic_arc_length(
    p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D, num_samples: int
) -> Points2D:
    """Sample a cubic bezier at equal arc-length intervals.

    Uses adaptive sampling to find t values that produce evenly-spaced points.
    """
    if num_samples <= 1:
        return [p0]

    # Build arc-length lookup table
    table_size = max(100, num_samples * 5)
    arc_lengths = [0.0]
    prev = p0

    for i in range(1, table_size + 1):
        t = i / table_size
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        t2 = t * t
        t3 = t2 * t
        x = mt3 * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t3 * p3.x
        y = mt3 * p0.y + 3 * mt2 * t * p1.y + 3 * mt * t2 * p2.y + t3 * p3.y
        curr = Point2D(x, y)
        arc_lengths.append(arc_lengths[-1] + math.sqrt((curr.x - prev.x) ** 2 + (curr.y - prev.y) ** 2))
        prev = curr

    total_length = arc_lengths[-1]
    if total_length < 1e-10:
        return [p0] * num_samples

    # Sample at equal arc-length intervals
    points = []
    for i in range(num_samples):
        target_length = (i / num_samples) * total_length

        # Binary search for t
        low, high = 0, table_size
        while high - low > 1:
            mid = (low + high) // 2
            if arc_lengths[mid] < target_length:
                low = mid
            else:
                high = mid

        # Linear interpolation between table entries
        if high < len(arc_lengths) and arc_lengths[high] != arc_lengths[low]:
            frac = (target_length - arc_lengths[low]) / (arc_lengths[high] - arc_lengths[low])
            t = (low + frac) / table_size
        else:
            t = low / table_size

        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        t2 = t * t
        t3 = t2 * t
        x = mt3 * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t3 * p3.x
        y = mt3 * p0.y + 3 * mt2 * t * p1.y + 3 * mt * t2 * p2.y + t3 * p3.y
        points.append(Point2D(x, y))

    return points


def resample_to_vertex_count(points: Points2D, target_count: int) -> Points2D:
    """Resample a list of points to a specific vertex count using arc-length interpolation.

    Args:
        points: Input points (assumed to form a closed loop if first == last)
        target_count: Desired number of output vertices

    Returns:
        List of target_count Point2D vertices evenly spaced by arc length
    """
    if len(points) < 2:
        return [points[0]] * target_count if points else [Point2D(0, 0)] * target_count

    # Build arc-length table
    arc_lengths = [0.0]
    for i in range(1, len(points)):
        dx = points[i].x - points[i-1].x
        dy = points[i].y - points[i-1].y
        arc_lengths.append(arc_lengths[-1] + math.sqrt(dx * dx + dy * dy))

    total_length = arc_lengths[-1]
    if total_length < 1e-10:
        return [points[0]] * target_count

    # Sample at equal arc-length intervals
    result = []
    for i in range(target_count):
        target_length = (i / target_count) * total_length

        # Binary search for segment
        low, high = 0, len(arc_lengths) - 1
        while high - low > 1:
            mid = (low + high) // 2
            if arc_lengths[mid] <= target_length:
                low = mid
            else:
                high = mid

        # Linear interpolation within segment
        segment_start = arc_lengths[low]
        segment_end = arc_lengths[high]
        if segment_end - segment_start > 1e-10:
            t = (target_length - segment_start) / (segment_end - segment_start)
        else:
            t = 0.0

        p1 = points[low]
        p2 = points[high]
        x = p1.x + t * (p2.x - p1.x)
        y = p1.y + t * (p2.y - p1.y)
        result.append(Point2D(x, y))

    return result
