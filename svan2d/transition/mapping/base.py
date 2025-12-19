"""Base classes for generic M→N mapping

Provides a unified mapper interface that works on any positionable items:
- States (letters in word morphing)
- VertexLoops (holes within shapes)
- Any other type with a position

The key abstraction is Match, which represents what happens to each item:
- start=item, end=item: morphing between two items
- start=item, end=None: destruction (fade out)
- start=None, end=item: creation (fade in)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic, List, Optional, Callable

from svan2d.core.point2d import Point2D

T = TypeVar('T')


@dataclass
class Match(Generic[T]):
    """A matched pair of items for interpolation.

    Represents the relationship between a start and end item during morphing.

    Attributes:
        start: The starting item, or None for creation (fade in)
        end: The ending item, or None for destruction (fade out)

    Semantics:
        - start=A, end=B: Item A morphs into item B
        - start=A, end=None: Item A fades out at its position
        - start=None, end=B: Item B fades in at its position
        - start=None, end=None: Invalid (not allowed)
    """
    start: Optional[T]
    end: Optional[T]

    def __post_init__(self):
        if self.start is None and self.end is None:
            raise ValueError("Match cannot have both start and end as None")

    @property
    def is_creation(self) -> bool:
        """True if this is a creation (start is None)."""
        return self.start is None

    @property
    def is_destruction(self) -> bool:
        """True if this is a destruction (end is None)."""
        return self.end is None

    @property
    def is_morph(self) -> bool:
        """True if this is a morph between two items."""
        return self.start is not None and self.end is not None


class Mapper(ABC):
    """Abstract base class for M→N mapping strategies.

    Mappers determine how items are matched during M→N transitions.
    Different strategies produce different visual effects:

    - SimpleMapper: No matching, all old items fade out, all new fade in
    - GreedyMapper: Match each item to its nearest neighbor
    - ClusteringMapper: Group nearby items together for balanced matching

    The mapper receives two lists of items and a position extractor function,
    and returns a list of Match objects describing how each item should transition.

    Example:
        # For states (letters)
        mapper.map(states1, states2, lambda s: s.pos)

        # For holes (vertex loops)
        mapper.map(holes1, holes2, lambda h: h.centroid())
    """

    @abstractmethod
    def map(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Map items for M→N morphing.

        Args:
            start_items: Items at the beginning of the transition
            end_items: Items at the end of the transition
            get_position: Function to extract position from an item

        Returns:
            List of Match objects describing the transition.
        """
        pass
