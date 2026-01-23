"""Hungarian algorithm mapping strategy

Optimal mapping using the Hungarian (Munkres) algorithm for globally
minimal distance assignment.

Requires scipy for the linear_sum_assignment implementation.
"""

from __future__ import annotations

from typing import Callable, List, TypeVar

from svan2d.core.point2d import Point2D

from .base import Mapper, Match

T = TypeVar('T')

# Try to import scipy
try:
    from scipy.optimize import linear_sum_assignment
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class HungarianMapper(Mapper):
    """Optimal mapping using Hungarian algorithm.

    Uses the Hungarian (Munkres) algorithm for globally optimal assignment.
    Minimizes total distance across all pairings, unlike greedy matching
    which may get stuck in local minima.

    Algorithm:
        1. Build cost matrix of distances between all item pairs
        2. For N!=M cases, replicate items to create square matrix
        3. Apply Hungarian algorithm to find minimum-cost perfect matching
        4. Map assignments back to original items

    For N>M (merging): Multiple start items morph to same end item
    For N<M (splitting): Same start item morphs to multiple end items
    For N=M: Direct optimal 1:1 assignment

    Advantages over greedy:
        - Globally optimal (minimum total distance)
        - Better results when items are clustered or evenly spaced
        - More predictable behavior

    Disadvantages:
        - Slower: O(n^3) vs O(n^2) for greedy
        - Requires scipy (optional dependency)

    Requires: scipy.optimize.linear_sum_assignment
    """

    def map(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Map items using Hungarian algorithm for optimal assignment."""
        if not SCIPY_AVAILABLE:
            raise ImportError(
                "Hungarian mapper requires scipy. Install it with:\n"
                "  pip install scipy\n\n"
                "Or use a different mapper:\n"
                "  mapper=ClusteringMapper()  # or GreedyMapper()"
            )

        n_start = len(start_items)
        n_end = len(end_items)

        if n_start == 0 and n_end == 0:
            return []

        if n_start == 0:
            return [Match(start=None, end=item) for item in end_items]

        if n_end == 0:
            return [Match(start=item, end=None) for item in start_items]

        if n_start == n_end:
            return self._match_equal(start_items, end_items, get_position)
        elif n_start < n_end:
            return self._match_split(start_items, end_items, get_position)
        else:
            return self._match_merge(start_items, end_items, get_position)

    def _match_equal(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Hungarian matching for equal counts (N=M)."""
        positions1 = [get_position(item) for item in start_items]
        positions2 = [get_position(item) for item in end_items]

        # Build cost matrix
        cost_matrix = []
        for p1 in positions1:
            row = [p1.distance_to(p2) for p2 in positions2]
            cost_matrix.append(row)

        # Apply Hungarian algorithm
        row_indices, col_indices = linear_sum_assignment(cost_matrix)  # type: ignore[reportPossiblyUnboundVariable]

        # Build matches
        matches = []
        for i, j in zip(row_indices, col_indices):
            matches.append(Match(start=start_items[i], end=end_items[j]))

        return matches

    def _match_split(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Hungarian matching when splitting (N < M).

        Each start item may morph to multiple end items.
        """
        n_start = len(start_items)
        n_end = len(end_items)

        positions1 = [get_position(item) for item in start_items]
        positions2 = [get_position(item) for item in end_items]

        # Build M x M cost matrix by replicating start items
        # source_map[row] = index into start_items
        cost_matrix = []
        source_map = []

        for _ in range((n_end + n_start - 1) // n_start):  # Enough replications
            for i in range(n_start):
                if len(cost_matrix) >= n_end:
                    break
                row = [positions1[i].distance_to(p2) for p2 in positions2]
                cost_matrix.append(row)
                source_map.append(i)

        cost_matrix = cost_matrix[:n_end]
        source_map = source_map[:n_end]

        # Apply Hungarian algorithm
        row_indices, col_indices = linear_sum_assignment(cost_matrix)  # type: ignore[reportPossiblyUnboundVariable]

        # Build matches (start items may appear multiple times)
        matches = []
        for i, j in zip(row_indices, col_indices):
            matches.append(Match(start=start_items[source_map[i]], end=end_items[j]))

        return matches

    def _match_merge(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Hungarian matching when merging (N > M).

        Multiple start items may morph to the same end item.
        """
        n_start = len(start_items)
        n_end = len(end_items)

        positions1 = [get_position(item) for item in start_items]
        positions2 = [get_position(item) for item in end_items]

        # Build N x N cost matrix by replicating end items
        # dest_map[col] = index into end_items
        dest_map = []

        for _ in range((n_start + n_end - 1) // n_end):  # Enough replications
            for j in range(n_end):
                if len(dest_map) >= n_start:
                    break
                dest_map.append(j)

        dest_map = dest_map[:n_start]

        # Build cost matrix
        cost_matrix = []
        for p1 in positions1:
            row = [p1.distance_to(positions2[dest_map[col]]) for col in range(n_start)]
            cost_matrix.append(row)

        # Apply Hungarian algorithm
        row_indices, col_indices = linear_sum_assignment(cost_matrix)  # type: ignore[reportPossiblyUnboundVariable]

        # Build matches (end items may appear multiple times)
        matches = []
        for i, j in zip(row_indices, col_indices):
            matches.append(Match(start=start_items[i], end=end_items[dest_map[j]]))

        return matches
