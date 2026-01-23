"""Angular alignment strategy for closed shapes

This module provides angular-based alignment for closed ↔ closed shape morphing.
Uses centroid-based angular positions to find optimal vertex correspondence.
"""

from __future__ import annotations

import inspect
import math
from typing import List, Optional, Tuple, Union

from svan2d.component.vertex import (
    angle_distance,
    angle_from_centroid,
    centroid,
)
from svan2d.component.vertex.vertex_utils import rotate_list, rotate_vertices
from svan2d.core.point2d import Point2D, Points2D

from .base import AlignmentContext, VertexAligner
from .norm import AlignmentNorm, AngularDistanceFn, NormSpec


class AngularAligner(VertexAligner):
    """Angular alignment based on centroid positions

    Uses angular alignment based on vertex positions relative to centroids.
    Rotates the second vertex list to minimize total angular distance.
    Best for closed ↔ closed shape morphing.

    Algorithm:
    1. Apply shape rotations to both vertex lists
    2. Calculate centroids for each shape
    3. Compute angular positions of each vertex relative to its centroid
    4. Try all possible vertex offset rotations
    5. Select offset that minimizes total angular distance (using specified norm)
    6. Return original vertices with selected offset applied to verts2

    Performance: O(n²) - tries n offsets, evaluates n vertices each
    """

    def __init__(
        self, norm: Union[str, AlignmentNorm, AngularDistanceFn] = AlignmentNorm.L1
    ):
        """
        Initialize angular aligner with distance norm.

        Args:
            norm: Distance metric for alignment
                - "l1" or AlignmentNorm.L1: Sum of angular differences (default)
                - "l2" or AlignmentNorm.L2: Root mean square angular distance
                - "linf" or AlignmentNorm.LINF: Maximum angular difference
                - Callable: Custom distance function(angles1, angles2, offset) -> float
        """
        if callable(norm):
            # Validate callable signature
            sig = inspect.signature(norm)
            if len(sig.parameters) != 3:
                raise TypeError(
                    f"Custom distance function must accept 3 parameters: "
                    f"(angles1, angles2, offset), got {len(sig.parameters)}"
                )
            self.norm = "custom"
            self._distance_fn = norm
        elif isinstance(norm, (str, AlignmentNorm)):
            self.norm = norm
            self._distance_fn = self._resolve_distance_function(norm)
        else:
            raise TypeError(
                f"norm must be str, AlignmentNorm, or callable, "
                f"got {type(norm).__name__}"
            )

    def _resolve_distance_function(
        self, norm: Union[str, AlignmentNorm]
    ) -> AngularDistanceFn:
        """Convert norm spec to actual distance function"""
        # Normalize string to enum
        if isinstance(norm, str):
            try:
                norm = AlignmentNorm(norm.lower())
            except ValueError:
                raise ValueError(
                    f"Invalid norm '{norm}'. Valid options: 'l1', 'l2', 'linf'"
                )

        # Return built-in function
        if norm == AlignmentNorm.L1:
            return self._l1_distance
        elif norm == AlignmentNorm.L2:
            return self._l2_distance
        elif norm == AlignmentNorm.LINF:
            return self._linf_distance
        else:
            raise ValueError(f"Unknown norm: {norm}")

    def _l1_distance(
        self, angles1: List[float], angles2: List[float], offset: int
    ) -> float:
        """Sum of absolute angular differences (L1 norm)"""
        n = len(angles1)
        return sum(
            angle_distance(angles1[i], angles2[(i + offset) % n]) for i in range(n)
        )

    def _l2_distance(
        self, angles1: List[float], angles2: List[float], offset: int
    ) -> float:
        """Root mean square angular distance (L2 norm)"""
        n = len(angles1)
        return math.sqrt(
            sum(
                angle_distance(angles1[i], angles2[(i + offset) % n]) ** 2
                for i in range(n)
            )
        )

    def _linf_distance(
        self, angles1: List[float], angles2: List[float], offset: int
    ) -> float:
        """Maximum angular difference (L∞ norm, minimax)"""
        n = len(angles1)
        return max(
            angle_distance(angles1[i], angles2[(i + offset) % n]) for i in range(n)
        )

    def align(
        self,
        verts1: Points2D,
        verts2: Points2D,
        context: AlignmentContext,
        rotation_target: float | None = None,
    ) -> Tuple[Points2D, Points2D]:
        if len(verts1) != len(verts2):
            raise ValueError(
                f"Vertex lists must have same length: {len(verts1)} != {len(verts2)}"
            )

        if not verts1 or not verts2:
            return verts1, verts2

        # Use rotation_target if provided, otherwise use context rotations
        rot1 = context.rotation1
        rot2 = rotation_target if rotation_target is not None else context.rotation2

        verts1_work = rotate_vertices(verts1, rot1) if rot1 != 0 else verts1
        verts2_work = rotate_vertices(verts2, rot2) if rot2 != 0 else verts2

        # Calculate centroids
        c1 = centroid(verts1_work)
        c2 = centroid(verts2_work)

        # Get angular positions from centroids
        angles1 = [angle_from_centroid(v, c1) for v in verts1_work]
        angles2 = [angle_from_centroid(v, c2) for v in verts2_work]

        # Find rotation offset that minimizes total angular distance (using specified norm)
        n = len(verts2)
        best_offset = 0
        min_distance = float("inf")

        for offset in range(n):
            # Use configured distance function (L1, L2, L∞, or custom)
            total_dist = self._distance_fn(angles1, angles2, offset)

            if total_dist < min_distance:
                min_distance = total_dist
                best_offset = offset

        # Apply best offset to original vertices using in-place rotation
        if best_offset == 0:
            verts2_aligned = verts2
        else:
            verts2_aligned = rotate_list(verts2, best_offset)

        return verts1, verts2_aligned
