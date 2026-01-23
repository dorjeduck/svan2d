"""Vertex alignment strategies for morph interpolation

This package provides pluggable strategies for aligning vertex lists during
morphing. Different strategies are used based on whether shapes are open/closed.

Available aligners:
- AngularAligner: For closed ↔ closed shapes (centroid-based angular distance)
- EuclideanAligner: For open ↔ closed shapes (straight-line distance)
- SequentialAligner: For open ↔ open shapes (sequential with reversal detection)

Distance norms:
- AlignmentNorm.L1: Sum of distances (default, economical)
- AlignmentNorm.L2: Root mean square distance (balanced, statistically optimal)
- AlignmentNorm.LINF: Maximum distance (minimax, ensures fairness)

Factory function:
- get_aligner(closed1, closed2): Auto-selects appropriate aligner
"""

from .angular import AngularAligner
from .base import AlignmentContext, VertexAligner, get_aligner
from .euclidean import EuclideanAligner
from .norm import AlignmentNorm, AngularDistanceFn, EuclideanDistanceFn, NormSpec
from .sequential import SequentialAligner

__all__ = [
    "VertexAligner",
    "AlignmentContext",
    "get_aligner",
    "AngularAligner",
    "EuclideanAligner",
    "SequentialAligner",
    "AlignmentNorm",
    "AngularDistanceFn",
    "EuclideanDistanceFn",
    "NormSpec",
]
