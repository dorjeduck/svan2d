"""Per-field timeline interpolation for attribute keystates."""

from __future__ import annotations
from dataclasses import replace
from typing import Dict, List, Any, TYPE_CHECKING

from svan2d.transition import lerp
from svan2d.component import State

if TYPE_CHECKING:
    from svan2d.velement.keystate import KeyStates
    from svan2d.transition.easing_resolver import EasingResolver
    from svan2d.transition.interpolation_engine import InterpolationEngine


class AttributeTimelineResolver:
    """Handles per-field custom timelines.

    Attribute timelines allow individual fields to have independent
    keyframe timelines separate from the main element keystates.
    """

    def __init__(
        self,
        attribute_keystates: Dict[str, List],
        keystates: "KeyStates",
        easing_resolver: "EasingResolver",
        interpolation_engine: "InterpolationEngine",
    ) -> None:
        """Initialize the attribute timeline resolver.

        Args:
            attribute_keystates: Per-field keystate timelines {field_name: [(t, value), ...]}
            keystates: Main element keystates (for base state reference)
            easing_resolver: Easing resolver for fallback easing functions
            interpolation_engine: Interpolation engine for value interpolation
        """
        self.attribute_keystates = attribute_keystates
        self.keystates = keystates
        self.easing_resolver = easing_resolver
        self.interpolation_engine = interpolation_engine

    def apply_field_timelines(self, base_state: State, t: float) -> State:
        """Apply custom field timeline values on top of the base state.

        Args:
            base_state: State from main keystate interpolation
            t: Current animation time

        Returns:
            State with field timeline values applied
        """
        if not self.attribute_keystates:
            return base_state

        updates = {}
        for field_name in self.attribute_keystates.keys():
            updates[field_name] = self.get_field_value_at_time(field_name, t)

        return replace(base_state, **updates)

    def get_field_value_at_time(self, field_name: str, t: float) -> Any:
        """Get field value at time t from attribute_keystates.

        Attribute timelines extend their first/last values to 0.0/1.0 to ensure
        attributes always have values when the element exists.

        Args:
            field_name: Name of the field
            t: Animation time

        Returns:
            Interpolated field value
        """
        timeline = self.attribute_keystates[field_name]

        if not timeline:
            raise ValueError(f"Empty timeline for field '{field_name}'")

        # Attribute timelines extend to full range
        if t <= timeline[0][0]:
            return timeline[0][1]
        if t >= timeline[-1][0]:
            return timeline[-1][1]

        # Find the segment containing time t
        for i in range(len(timeline) - 1):
            item1 = timeline[i]
            t1, val1, *rest1 = item1
            easing1 = rest1[0] if rest1 else None

            item2 = timeline[i + 1]
            t2, val2, *rest2 = item2

            if t1 <= t <= t2:
                if t1 == t2:
                    return val2

                segment_duration = t2 - t1
                segment_t = (t - t1) / segment_duration

                # Get easing function (use segment-level or fallback)
                if easing1 is None:
                    base_state = self.keystates[0].state if self.keystates else None
                    easing_func = self.easing_resolver.get_easing_for_field_timeline(
                        base_state, field_name
                    )
                else:
                    easing_func = easing1

                eased_t = easing_func(segment_t) if easing_func else segment_t

                # Interpolate the value
                base_state = self.keystates[0].state if self.keystates else None
                if not base_state:
                    return lerp(val1, val2, eased_t)

                return self.interpolation_engine.interpolate_value(
                    base_state, base_state, field_name, val1, val2, eased_t
                )

        return timeline[-1][1]
