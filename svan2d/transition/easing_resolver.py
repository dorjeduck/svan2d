"""Easing function resolution with 3-level priority system"""

from __future__ import annotations

from typing import Callable

from svan2d.transition import easing

# Easing function can return float (1D) or tuple[float, float] (2D for Point2D)
EasingFunction = Callable[[float], float | tuple[float, float]]


class EasingResolver:
    """
    Resolves easing functions for field animations using a 3-level priority system.

    Priority (highest to lowest):
    1. Segment-level per-field easing overrides (easing_dict)
    2. Segment-level blanket easing (easing)
    3. Instance-level field easing (attribute_easing dict)
    4. Global default (linear)
    """

    def __init__(
        self,
        attribute_easing_dict: dict[str, EasingFunction] | None = None,
    ):
        self.attribute_easing = attribute_easing_dict or {}

    def get_easing_for_field(
        self,
        field_name: str,
        segment_easing_overrides: dict[str, EasingFunction] | None = None,
        segment_easing: EasingFunction | None = None,
    ) -> EasingFunction:
        if segment_easing_overrides and field_name in segment_easing_overrides:
            return segment_easing_overrides[field_name]

        if segment_easing is not None:
            return segment_easing

        if field_name in self.attribute_easing:
            return self.attribute_easing[field_name]

        return easing.linear

    def get_easing_for_field_timeline(
        self,
        field_name: str,
    ) -> EasingFunction:
        if field_name in self.attribute_easing:
            return self.attribute_easing[field_name]

        return easing.linear
