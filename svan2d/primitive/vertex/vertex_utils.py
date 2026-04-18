"""Utility functions for vertex operations"""

from __future__ import annotations

import math
from statistics import mean

from svan2d.core.point2d import Point2D, Points2D


def centroid(vertices: Points2D) -> Point2D:
    """Calculate the centroid (center of mass) of a set of vertices

    Args:
        vertices: List of Point2D objects

    Returns:
        Point2D centroid position
    """
    if not vertices:
        return Point2D(0.0, 0.0)

    xs, ys = zip(*vertices)
    return Point2D(mean(xs), mean(ys))


def angle_from_centroid(vertex: Point2D, center: Point2D) -> float:
    """Calculate angle of vertex from centroid in Svan2D coordinates

    Svan2D uses: 0° = East, 90° = North (up), counter-clockwise positive

    Args:
        vertex: (x, y) position
        center: (cx, cy) centroid position

    Returns:
        Angle in radians (0 to 2π)
    """
    dx = vertex.x - center.x
    dy = vertex.y - center.y

    # Standard math angle: from East (0°), counter-clockwise positive
    # Negate dy because vertices are in SVG local coords (Y-down)
    angle = math.atan2(-dy, dx)

    # Ensure positive angle
    if angle < 0:
        angle += 2 * math.pi

    return angle


def angle_distance(a1: float, a2: float) -> float:
    """Calculate shortest angular distance between two angles

    Args:
        a1, a2: Angles in radians

    Returns:
        Shortest distance in radians (always positive)
    """
    diff = (a2 - a1) % (2 * math.pi)
    if diff > math.pi:
        diff = 2 * math.pi - diff
    return diff


def rotate_vertices(vertices: Points2D, rotation_degrees: float) -> Points2D:
    """Rotate vertices by given angle

    Args:
        vertices: List of (x, y) tuples
        rotation_degrees: Rotation in degrees (0° = East, counter-clockwise positive)

    Returns:
        Rotated vertices
    """
    
    if rotation_degrees == 0:
        return vertices
    
    # Negate rotation: vertices are in SVG local Y-down; user CCW = SVG CW
    angle_rad = math.radians(-rotation_degrees)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    rotated = []
    for x, y in vertices:
        # Standard rotation matrix applied with negated angle for Cartesian convention
        rx = x * cos_a - y * sin_a
        ry = x * sin_a + y * cos_a
        rotated.append(Point2D(rx, ry))

    return rotated


def rotate_list(lst, offset):
    """Return a new list rotated left by offset positions.

    Args:
        lst: list to rotate (can contain any elements)
        offset: number of positions to rotate (positive = left rotation)

    Example:
        rotate_list([1,2,3,4,5], 2) -> [3,4,5,1,2]
    """
    if not lst:
        return []

    n = len(lst)
    offset %= n
    if offset == 0:
        return lst.copy()

    return lst[offset:] + lst[:offset]


