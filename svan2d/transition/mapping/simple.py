"""Simple mapping strategy - pure crossfade

All old items fade out at their positions, all new items fade in at their
positions. No spatial matching or morphing between items.
"""

from __future__ import annotations

from typing import Callable, List, TypeVar

from svan2d.core.point2d import Point2D

from .base import Mapper, Match

T = TypeVar('T')


class SimpleMapper(Mapper):
    """Simplest mapping - all old disappear, all new appear.

    Visual effect: Clean crossfade where old items fade out at their
    positions and new items fade in at their positions. No morphing
    or movement between items.

    Example:
        "AB" → "XYZ"
        - A fades out at A's position
        - B fades out at B's position
        - X fades in at X's position
        - Y fades in at Y's position
        - Z fades in at Z's position

    Use cases:
        - Completely different layouts where morphing would look awkward
        - Clean "before/after" transitions
        - When you want items to fade independently
    """

    def map(
        self,
        start_items: List[T],
        end_items: List[T],
        get_position: Callable[[T], Point2D]
    ) -> List[Match[T]]:
        """Map items with no correspondence - pure crossfade.

        All start items become destructions (fade out).
        All end items become creations (fade in).
        """
        matches = []

        for item in start_items:
            matches.append(Match(start=item, end=None))

        for item in end_items:
            matches.append(Match(start=None, end=item))

        return matches
