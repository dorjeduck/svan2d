"""Composite filter"""

from __future__ import annotations

from dataclasses import dataclass


import drawsvg as dw

from .base import Filter


@dataclass(frozen=True)
class CompositeFilter(Filter):
    """Composite multiple filters together

    Args:
        filters: Tuple of filters to apply in sequence

    Example:
        blur = GaussianBlurFilter(std_deviation=3.0)
        shadow = DropShadowFilter(dx=5, dy=5, std_deviation=2)
        composite = CompositeFilter(filters=(blur, shadow))
    """

    filters: tuple[Filter, ...]

    def __post_init__(self):
        if not self.filters:
            raise ValueError("CompositeFilter must have at least one filter")

    def to_drawsvg(self) -> dw.FilterItem:
        """Return the first filter's FilterItem.

        Full composition (all filters) is handled at the renderer level,
        which iterates ``self.filters`` directly.
        """
        return self.filters[0].to_drawsvg()

    def interpolate(self, other: Filter, t: float):
        """Interpolate between two CompositeFilter instances"""
        if not isinstance(other, CompositeFilter):
            return self if t < 0.5 else other

        # If both have same number of filters, interpolate pairwise
        if len(self.filters) == len(other.filters):
            interpolated_filters = tuple(
                self.filters[i].interpolate(other.filters[i], t)
                for i in range(len(self.filters))
            )
            return CompositeFilter(filters=interpolated_filters)

        # Otherwise, step interpolation
        return self if t < 0.5 else other
