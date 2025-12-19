"""Clustering-based mapping strategy

Uses k-means clustering for balanced grouping when item counts differ.
Spatially close items are grouped together for morphing.
"""

from __future__ import annotations
import random
from typing import TypeVar, List, Callable

from svan2d.core.point2d import Point2D
from .base import Mapper, Match
from .greedy import GreedyMapper

T = TypeVar('T')


class ClusteringMapper(Mapper):
    """Match items using k-means clustering for balanced grouping.

    When item counts differ (M→N), uses clustering to group the larger
    set into clusters, then matches clusters to the smaller set.

    Algorithm:
        1. For N > M (merging): Cluster N items into M groups
        2. For N < M (splitting): Cluster M items into N groups
        3. For N = M: Falls back to greedy 1:1 matching

    Args:
        max_iterations: Maximum k-means iterations (default: 50)
        random_seed: Seed for reproducible clustering (default: 42)
    """

    def __init__(self, max_iterations: int = 50, random_seed: int = 42):
        self.max_iterations = max_iterations
        self.random_seed = random_seed
        self._greedy = GreedyMapper()

    def map(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Map items using k-means clustering."""
        if not start_items and not end_items:
            return []

        if not start_items:
            return [Match(start=None, end=item) for item in end_items]

        if not end_items:
            return [Match(start=item, end=None) for item in start_items]

        n_start = len(start_items)
        n_end = len(end_items)

        if n_start == n_end:
            return self._greedy.map(start_items, end_items, get_position)
        elif n_start > n_end:
            return self._match_merge(start_items, end_items, get_position)
        else:
            return self._match_split(start_items, end_items, get_position)

    def _match_merge(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Match when merging (more start items than end items)."""
        n_clusters = len(end_items)
        positions = [get_position(item) for item in start_items]

        clusters = self._kmeans(positions, n_clusters)

        matches = []
        used_end: set = set()

        for cluster_idx in range(n_clusters):
            cluster_items = [
                start_items[i] for i, c in enumerate(clusters) if c == cluster_idx
            ]
            if not cluster_items:
                continue

            centroid = self._compute_centroid(
                [get_position(item) for item in cluster_items]
            )

            best_end_idx = -1
            best_dist = float('inf')
            for i, end in enumerate(end_items):
                if i in used_end:
                    continue
                dist = centroid.distance_to(get_position(end))
                if dist < best_dist:
                    best_dist = dist
                    best_end_idx = i

            if best_end_idx >= 0:
                used_end.add(best_end_idx)
                end_item = end_items[best_end_idx]

                # All items in cluster morph to the same end item
                for item in cluster_items:
                    matches.append(Match(start=item, end=end_item))

        for i, end in enumerate(end_items):
            if i not in used_end:
                matches.append(Match(start=None, end=end))

        return matches

    def _match_split(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Match when splitting (more end items than start items)."""
        n_clusters = len(start_items)
        positions = [get_position(item) for item in end_items]

        clusters = self._kmeans(positions, n_clusters)

        matches = []
        used_start: set = set()

        for cluster_idx in range(n_clusters):
            cluster_items = [
                end_items[i] for i, c in enumerate(clusters) if c == cluster_idx
            ]
            if not cluster_items:
                continue

            centroid = self._compute_centroid(
                [get_position(item) for item in cluster_items]
            )

            best_start_idx = -1
            best_dist = float('inf')
            for i, start in enumerate(start_items):
                if i in used_start:
                    continue
                dist = centroid.distance_to(get_position(start))
                if dist < best_dist:
                    best_dist = dist
                    best_start_idx = i

            if best_start_idx >= 0:
                used_start.add(best_start_idx)
                start_item = start_items[best_start_idx]

                # All items in cluster morph from the same start item
                for item in cluster_items:
                    matches.append(Match(start=start_item, end=item))

        for i, start in enumerate(start_items):
            if i not in used_start:
                matches.append(Match(start=start, end=None))

        return matches

    def _kmeans(self, positions: List[Point2D], k: int) -> List[int]:
        """Run k-means clustering on positions."""
        if k <= 0 or not positions:
            return []

        if k >= len(positions):
            return list(range(len(positions)))

        random.seed(self.random_seed)

        indices = random.sample(range(len(positions)), k)
        centroids = [positions[i] for i in indices]

        assignments = [0] * len(positions)

        for _ in range(self.max_iterations):
            new_assignments = []
            for pos in positions:
                best_cluster = 0
                best_dist = float('inf')
                for c, centroid in enumerate(centroids):
                    dist = pos.distance_to(centroid)
                    if dist < best_dist:
                        best_dist = dist
                        best_cluster = c
                new_assignments.append(best_cluster)

            if new_assignments == assignments:
                break
            assignments = new_assignments

            for c in range(k):
                cluster_points = [
                    positions[i] for i, a in enumerate(assignments) if a == c
                ]
                if cluster_points:
                    centroids[c] = self._compute_centroid(cluster_points)

        return assignments

    def _compute_centroid(self, positions: List[Point2D]) -> Point2D:
        """Compute centroid of a list of positions."""
        if not positions:
            return Point2D(0, 0)
        x = sum(p.x for p in positions) / len(positions)
        y = sum(p.y for p in positions) / len(positions)
        return Point2D(x, y)
