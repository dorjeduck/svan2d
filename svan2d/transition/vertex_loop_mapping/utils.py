"""Utility functions for hole mapping

This module provides helper functions used by vertex_loop mapping strategies.
"""

from __future__ import annotations
from enum import Enum
from typing import Union, Callable
import math

from svan2d.component.vertex import VertexLoop
from svan2d.core.point2d import Point2D


class LoopMapperNorm(Enum):
    """Distance norms for vertex loop mapping

    Different norms produce different matching behaviors:
    - L1: Manhattan distance (sum of absolute differences)
    - L2: Euclidean distance (default, straight-line)
    - LINF: Chebyshev distance (maximum of absolute differences)
    """
    L1 = "l1"
    L2 = "l2"
    LINF = "linf"


# Type alias for custom distance functions
DistanceFn = Callable[[Point2D, Point2D], float]

# Union type for norm specification
NormSpec = Union[str, LoopMapperNorm, DistanceFn]


def distance_l1(p1: Point2D, p2: Point2D) -> float:
    """Manhattan (L1) distance between two points"""
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)


def distance_l2(p1: Point2D, p2: Point2D) -> float:
    """Euclidean (L2) distance between two points"""
    return math.hypot(p1.x - p2.x, p1.y - p2.y)


def distance_linf(p1: Point2D, p2: Point2D) -> float:
    """Chebyshev (L-infinity) distance between two points"""
    return max(abs(p1.x - p2.x), abs(p1.y - p2.y))


def resolve_distance_fn(norm: NormSpec) -> DistanceFn:
    """Resolve norm specification to a distance function

    Args:
        norm: One of:
            - "l1", "l2", "linf" (strings)
            - LoopMapperNorm.L1, L2, LINF (enum)
            - Custom callable(Point2D, Point2D) -> float

    Returns:
        Distance function
    """
    if callable(norm):
        return norm

    # Normalize to enum
    if isinstance(norm, str):
        try:
            norm = LoopMapperNorm(norm.lower())
        except ValueError:
            raise ValueError(f"Unknown norm: {norm}. Use 'l1', 'l2', or 'linf'")

    if norm == LoopMapperNorm.L1:
        return distance_l1
    elif norm == LoopMapperNorm.L2:
        return distance_l2
    elif norm == LoopMapperNorm.LINF:
        return distance_linf
    else:
        raise ValueError(f"Unknown norm: {norm}")


def create_zero_vertex_loop(reference_vertex_loop: VertexLoop) -> VertexLoop:
    """Create a zero-sized vertex_loop at the centroid of the reference vertex_loop

    All vertices are placed at the same point (the centroid), making a
    degenerate vertex_loop that can smoothly interpolate to/from the reference.

    This is used for vertex_loop creation/destruction scenarios:
    - N vertex loops → 0  vertex_loops : Each source vertex_loop shrinks to zero at its centroid
    - 0 vertex loops → M  vertex_loops : Each dest vertex_loop grows from zero at its centroid

    Args:
        reference_vertex_loop: vertex_loop to use as reference for position and vertex count

    Returns:
        Zero-sized VertexLoop with same vertex count as reference

    Example:
        >>> vertex_loop = VertexLoop([(0, 0), (10, 0), (10, 10), (0, 10)], closed=True)
        >>> zero = create_zero_vertex_loop(vertex_loop)
        >>> zero.vertices  # All at centroid (5, 5)
        [(5.0, 5.0), (5.0, 5.0), (5.0, 5.0), (5.0, 5.0)]
    """
    center = reference_vertex_loop.centroid()
    zero_vertices = [center] * len(reference_vertex_loop.vertices)
    return VertexLoop(zero_vertices, closed=True)
