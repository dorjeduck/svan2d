"""Greedy nearest-neighbor mapping strategy

Matches items using a greedy approach based on spatial distance.
Each item morphs to its nearest available neighbor.
"""

from __future__ import annotations

from typing import Callable, List, Set, TypeVar

from svan2d.core.point2d import Point2D

from .base import Mapper, Match

T = TypeVar('T')


class GreedyMapper(Mapper):
    """Match items using greedy nearest-neighbor strategy.

    Uses spatial distance to greedily match items. When counts differ,
    extra items on one side become creations or destructions.

    Algorithm:
        1. For the smaller set, greedily assign each to nearest in larger set
        2. Remaining unmatched items become creations or destructions

    Visual effect: Items morph to their spatially nearest counterparts.

    Example:
        "AB" → "XYZ" (if X is near A, Y is near B, Z is far)
        - A morphs to X
        - B morphs to Y
        - Z fades in (creation)
    """

    def map(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Map items using greedy nearest-neighbor matching."""
        if not start_items and not end_items:
            return []

        if not start_items:
            return [Match(start=None, end=item) for item in end_items]

        if not end_items:
            return [Match(start=item, end=None) for item in start_items]

        n_start = len(start_items)
        n_end = len(end_items)

        if n_start == n_end:
            return self._match_equal(start_items, end_items, get_position)
        elif n_start < n_end:
            return self._match_fewer_start(start_items, end_items, get_position)
        else:
            return self._match_fewer_end(start_items, end_items, get_position)

    def _match_equal(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Match equal-sized lists 1:1 using greedy assignment."""
        matches = []
        used_end: Set[int] = set()

        for start in start_items:
            start_pos = get_position(start)

            best_idx = -1
            best_dist = float('inf')
            for i, end in enumerate(end_items):
                if i in used_end:
                    continue
                dist = start_pos.distance_to(get_position(end))
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i

            if best_idx >= 0:
                used_end.add(best_idx)
                matches.append(Match(start=start, end=end_items[best_idx]))

        return matches

    def _match_fewer_start(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Match when there are fewer start items than end items."""
        matches = []
        used_end: Set[int] = set()

        for start in start_items:
            start_pos = get_position(start)

            best_idx = -1
            best_dist = float('inf')
            for i, end in enumerate(end_items):
                if i in used_end:
                    continue
                dist = start_pos.distance_to(get_position(end))
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i

            if best_idx >= 0:
                used_end.add(best_idx)
                matches.append(Match(start=start, end=end_items[best_idx]))

        for i, end in enumerate(end_items):
            if i not in used_end:
                matches.append(Match(start=None, end=end))

        return matches

    def _match_fewer_end(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Match when there are fewer end items than start items."""
        matches = []
        used_start: Set[int] = set()

        for end in end_items:
            end_pos = get_position(end)

            best_idx = -1
            best_dist = float('inf')
            for i, start in enumerate(start_items):
                if i in used_start:
                    continue
                dist = end_pos.distance_to(get_position(start))
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i

            if best_idx >= 0:
                used_start.add(best_idx)
                matches.append(Match(start=start_items[best_idx], end=end))

        for i, start in enumerate(start_items):
            if i not in used_start:
                matches.append(Match(start=start, end=None))

        return matches
