"""Explicit index-based mapping strategy.

Maps items by index order or user-specified pairs, ignoring spatial position.
Ideal for morphing the same word between fonts where glyph correspondence is known.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple, TypeVar

from svan2d.core.point2d import Point2D

from .base import Mapper, Match

T = TypeVar("T")


class ExplicitMapper(Mapper):
    """Map items by explicit index pairs or sequential index order.

    When no pairs are specified, maps by index: start[0]→end[0], start[1]→end[1], etc.
    Extra items on either side become creations or destructions.

    When pairs are specified, maps exactly as given. Unmentioned items become
    creations or destructions.

    Examples:
        # Sequential (same word, different fonts):
        ExplicitMapper()

        # Explicit pairs (start_index → end_index):
        ExplicitMapper(pairs=[(0, 2), (1, 0), (2, 1)])
    """

    def __init__(self, pairs: Optional[Sequence[Tuple[int, int]]] = None):
        """
        Args:
            pairs: Optional list of (start_index, end_index) tuples.
                   If None, maps sequentially by index.
        """
        self._pairs = pairs

    def map(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D],
    ) -> List[Match[T]]:
        """Map items by index order or explicit pairs."""
        if self._pairs is not None:
            return self._map_explicit(start_items, end_items)
        return self._map_sequential(start_items, end_items)

    def _map_sequential(
        self, start_items: List[T], end_items: List[T]
    ) -> List[Match[T]]:
        """Map by index: start[i] → end[i]. Extras become creation/destruction."""
        matches: List[Match[T]] = []
        n_common = min(len(start_items), len(end_items))

        for i in range(n_common):
            matches.append(Match(start=start_items[i], end=end_items[i]))

        for i in range(n_common, len(start_items)):
            matches.append(Match(start=start_items[i], end=None))

        for i in range(n_common, len(end_items)):
            matches.append(Match(start=None, end=end_items[i]))

        return matches

    def _map_explicit(
        self, start_items: List[T], end_items: List[T]
    ) -> List[Match[T]]:
        """Map by user-specified (start_index, end_index) pairs."""
        assert self._pairs is not None
        matches: List[Match[T]] = []
        used_start: set[int] = set()
        used_end: set[int] = set()

        for si, ei in self._pairs:
            if si >= len(start_items) or ei >= len(end_items):
                raise IndexError(
                    f"Pair ({si}, {ei}) out of range: "
                    f"start has {len(start_items)}, end has {len(end_items)} items"
                )
            matches.append(Match(start=start_items[si], end=end_items[ei]))
            used_start.add(si)
            used_end.add(ei)

        # Unmatched items become destructions/creations
        for i in range(len(start_items)):
            if i not in used_start:
                matches.append(Match(start=start_items[i], end=None))

        for i in range(len(end_items)):
            if i not in used_end:
                matches.append(Match(start=None, end=end_items[i]))

        return matches
