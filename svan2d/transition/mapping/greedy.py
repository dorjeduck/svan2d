"""Greedy nearest-neighbor mapping strategy.

Matches items using a greedy approach based on spatial distance.
Each item morphs to its nearest available neighbor.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from svan2d.core.point2d import Point2D

from .base import Mapper, Match

T = TypeVar("T")


def _greedy_assign(
    seekers: list[T],
    candidates: list[T],
    get_position: Callable[[T], Point2D],
) -> tuple[list[tuple[T, T]], set[int]]:
    """Greedily assign each seeker to its nearest unused candidate.

    Returns:
        (pairs, used_indices) — matched (seeker, candidate) pairs
        and the set of candidate indices that were used.
    """
    pairs: list[tuple[T, T]] = []
    used: set[int] = set()

    for seeker in seekers:
        seeker_pos = get_position(seeker)
        best_idx = -1
        best_dist = float("inf")
        for i, candidate in enumerate(candidates):
            if i in used:
                continue
            dist = seeker_pos.distance_to(get_position(candidate))
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        if best_idx >= 0:
            used.add(best_idx)
            pairs.append((seeker, candidates[best_idx]))

    return pairs, used


class GreedyMapper(Mapper):
    """Match items using greedy nearest-neighbor strategy.

    Uses spatial distance to greedily match items. When counts differ,
    extra items on one side become creations or destructions.

    Algorithm:
        1. For the smaller set, greedily assign each to nearest in larger set
        2. Remaining unmatched items become creations or destructions

    Visual effect: Items morph to their spatially nearest counterparts.
    """

    def map(
        self,
        start_items: list[T],
        end_items: list[T],
        get_position: Callable[[T], Point2D],
    ) -> list[Match[T]]:
        """Map items using greedy nearest-neighbor matching."""
        if not start_items and not end_items:
            return []
        if not start_items:
            return [Match(start=None, end=item) for item in end_items]
        if not end_items:
            return [Match(start=item, end=None) for item in start_items]

        if len(start_items) <= len(end_items):
            # Iterate start → find nearest end
            pairs, used_end = _greedy_assign(start_items, end_items, get_position)
            matches = [Match(start=s, end=e) for s, e in pairs]
            for i, end in enumerate(end_items):
                if i not in used_end:
                    matches.append(Match(start=None, end=end))
        else:
            # Iterate end → find nearest start
            pairs, used_start = _greedy_assign(end_items, start_items, get_position)
            matches = [Match(start=s, end=e) for e, s in pairs]
            for i, start in enumerate(start_items):
                if i not in used_start:
                    matches.append(Match(start=start, end=None))

        return matches
