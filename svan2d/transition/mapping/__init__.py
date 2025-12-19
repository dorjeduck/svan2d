"""Generic M→N mapping strategies

Provides a unified mapper interface that works on any positionable items:
- States (letters in word morphing)
- VertexLoops (holes within shapes)
- Any other type with a position

Classes:
    Match: Represents a matched pair of items for interpolation
    Mapper: Abstract base class for mapping strategies
    SimpleMapper: No matching - all old disappear, all new appear
    GreedyMapper: Greedy nearest-neighbor matching
    ClusteringMapper: K-means clustering for balanced grouping
    HungarianMapper: Optimal assignment using Hungarian algorithm (requires scipy)
"""

from .base import Match, Mapper
from .simple import SimpleMapper
from .greedy import GreedyMapper
from .clustering import ClusteringMapper
from .hungarian import HungarianMapper

__all__ = [
    "Match",
    "Mapper",
    "SimpleMapper",
    "GreedyMapper",
    "ClusteringMapper",
    "HungarianMapper",
]
