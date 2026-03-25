"""Easing function resolution with 4-level priority system"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from svan2d.component.state.base import State

from svan2d.transition import easing

# Easing function can return float (1D) or tuple[float, float] (2D for Point2D)
EasingFunction = Callable[[float], float | tuple[float, float]]


class EasingResolver:
    """
    Resolves easing functions for field animations using a 5-level priority system.

    Priority (highest to lowest):
    1. Segment-level per-field easing overrides (easing_dict)
    2. Segment-level blanket easing (easing)
    3. Instance-level field easing (attribute_easing dict)
    4. State class default easing (State.DEFAULT_EASING)
    5. Global default (linear)
    """

    def __init__(
        self,
        attribute_easing_dict: dict[str, EasingFunction] | None = None,
    ):
        """
        Initialize the easing resolver.

        Args:
            attribute_easing_dict: Instance-level easing overrides for specific attributes
        """
        self.attribute_easing = attribute_easing_dict or {}

    def get_easing_for_field(
        self,
        state: State,
        field_name: str,
        segment_easing_overrides: dict[str, EasingFunction] | None = None,
        segment_easing: EasingFunction | None = None,
    ) -> EasingFunction:
        """
        Get the easing function for a field following the 5-level priority.

        Args:
            state: The state object containing the field
            field_name: Name of the field being animated
            segment_easing_overrides: Optional per-field segment-level easing overrides
            segment_easing: Optional blanket segment-level easing for all fields

        Returns:
            Easing function to apply
        """
        # Level 1: Segment-level per-field override (highest priority)
        if segment_easing_overrides and field_name in segment_easing_overrides:
            return segment_easing_overrides[field_name]

        # Level 2: Segment-level blanket easing
        if segment_easing is not None:
            return segment_easing

        # Level 3: Instance-level field easing
        if field_name in self.attribute_easing:
            return self.attribute_easing[field_name]

        # Level 4: State class default easing
        default_easing = getattr(state, "DEFAULT_EASING", {})
        if field_name in default_easing:
            return default_easing[field_name]

        # Level 5: Global default
        return easing.linear

    def get_easing_for_field_timeline(
        self,
        state: State | None,
        field_name: str,
    ) -> EasingFunction:
        """
        Get fallback easing for custom field timelines.

        Used when a field timeline segment doesn't specify its own easing.
        Uses instance-level or state-level defaults.

        Args:
            state: Optional state object for accessing class defaults
            field_name: Name of the field

        Returns:
            Easing function to apply
        """
        # Level 2: Instance-level field easing
        if field_name in self.attribute_easing:
            return self.attribute_easing[field_name]

        # Level 3: State class default easing (if state provided)
        if state:
            default_easing = getattr(state, "DEFAULT_EASING", {})
            if field_name in default_easing:
                return default_easing[field_name]

        # Level 4: Global default
        return easing.linear
