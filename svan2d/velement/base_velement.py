"""Base element class with shared keystate animation logic"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, List, Optional, Callable, Dict, Any, Tuple, TYPE_CHECKING
from dataclasses import replace
from enum import StrEnum

import drawsvg as dw


from svan2d.transition.align_vertices import (
    get_aligned_vertices,
)

from svan2d.transition import lerp, step, angle, inbetween, circular_midpoint

# Import the extracted modules
from svan2d.velement.keystate_parser import (
    parse_element_keystates,
    parse_attribute_keystates,
    FlexibleKeystateInput,
    AttributeKeyframeTuple,
)
from svan2d.velement.keystate import KeyState, KeyStates
from svan2d.transition.easing_resolver import EasingResolver
from svan2d.transition.interpolation_engine import InterpolationEngine


from svan2d.component import VertexState
from svan2d.component import State


class BaseVElement(ABC):
    """
    Abstract base class for all animatable elements.

    Provides shared keystate animation logic using a flexible, layered easing
    priority system and supporting custom field timelines.

    Architecture:
    - KeystateParser: Handles parsing and time distribution
    - EasingResolver: Manages 4-level easing priority system
    - InterpolationEngine: Handles state and value interpolation
    """

    def __init__(
        self,
        state: Optional[State] = None,
        keystates: Optional[Iterable[FlexibleKeystateInput]] = None,
        attribute_easing: Optional[Dict[str, Callable[[float], float]]] = None,
        attribute_keystates: Optional[Dict[str, List[AttributeKeyframeTuple]]] = None,
    ) -> None:
        """
        Initialize keystate animation system.

        Args:
            state: Single static state (mutually exclusive with keystates)
            keystates: List of states with optional timing/easing
            attribute_easing: Instance-level easing overrides for attributes
            attribute_keystates: Custom timelines for individual attributes
        """
        # Input validation for mutual exclusivity
        provided_inputs = [arg for arg in [state, keystates] if arg is not None]
        count = len(provided_inputs)

        if count == 0:
            raise ValueError(
                "VElement requires configuration: provide 'state' or 'keystates'."
            )
        if count > 1:
            raise ValueError(
                f"Conflicting inputs provided ({count} specified). "
                "Please specify only one of 'state' or 'keystates'."
            )

        # Initialize helper systems
        self.easing_resolver = EasingResolver(attribute_easing)
        self.interpolation_engine = InterpolationEngine(self.easing_resolver)

        # Store field keystates (will be parsed on first use)
        self.attribute_keystates_raw = attribute_keystates or {}
        self.attribute_keystates: Dict[str, List[AttributeKeyframeTuple]] = {}
        self.keystates: KeyStates = []

        # Parse and set keystates
        if state is not None:
            if isinstance(state, Iterable):
                raise ValueError("state must be a single State instance, not a list")
            self.set_state(state)
        elif keystates is not None:
            self.set_keystates(keystates)

        # Parse field keystates if provided
        if self.attribute_keystates_raw:
            self._parse_attribute_keystates()

    def set_state(self, state: State) -> None:
        """Set a single static state"""
        self.keystates = [KeyState(state=state, time=0.0)]

    def set_keystates(self, keystates: List[FlexibleKeystateInput]) -> None:
        """Set keystates using the flexible combined format"""
        if not keystates:
            raise ValueError("keystates cannot be empty")

        self.keystates = parse_element_keystates(keystates)

        if not self.keystates:
            raise ValueError("Keystates list could not be parsed.")

    def _parse_attribute_keystates(self) -> None:
        """Parse raw field keystates into normalized format"""
        for field_name, timeline in self.attribute_keystates_raw.items():
            if not timeline:
                raise ValueError(f"Empty timeline for field '{field_name}'")
            self.attribute_keystates[field_name] = parse_attribute_keystates(timeline)

    @abstractmethod
    def render(self) -> Optional[dw.DrawingElement]:
        """Render the element in its initial state (static rendering)"""
        if not self.keystates:
            raise ValueError("No state, states, or keystates set for rendering.")
        pass

    @abstractmethod
    def render_at_frame_time(
        self, t: float, drawing: Optional[dw.Drawing] = None
    ) -> Optional[dw.DrawingElement]:
        """Render the element at a specific animation time"""
        if not self.keystates:
            raise ValueError("No state, states, or keystates set for rendering.")
        pass

    def is_animatable(self) -> bool:
        """Check if this element can be animated"""
        return len(self.keystates) > 1 or bool(self.attribute_keystates)

    def _ensure_segment_preprocessed(self, i: int) -> None:
        """
        Ensure segment i→(i+1) has static alignment preprocessing applied.

        Only runs for non-rotating morphs (rotation doesn't change).
        Stores aligned contours in keystates for reuse across all frames.

        Args:
            i: Segment index (processes keystates[i] and keystates[i+1])
        """
        ks1 = self.keystates[i]
        ks2 = self.keystates[i + 1]

        state1, state2 = ks1.state, ks2.state
        t1, t2 = ks1.time, ks2.time

        # Check if preprocessing needed
        if not (
            isinstance(state1, VertexState)
            and isinstance(state2, VertexState)
            and state2._aligned_contours == None
        ):
            return  # Already preprocessed or not a vertex morph

        # Extract morphing config (prefer ks2's config)
        from svan2d.velement.keystate import Morphing

        morphing_config = ks2.morphing or ks1.morphing

        if isinstance(morphing_config, Morphing):
            morphing_dict = morphing_config.to_dict()
        elif isinstance(morphing_config, dict):
            morphing_dict = morphing_config
        else:
            morphing_dict = None

        # Only preprocess if rotation doesn't change
        # (rotating morphs use dynamic alignment per-frame)
        if state1.rotation != state2.rotation:
            return  # Skip static preprocessing for rotating morphs

        # Perform static alignment
        vertex_loop_mapper = (
            morphing_dict.get("vertex_loop_mapper") if morphing_dict else None
        )
        vertex_aligner = morphing_dict.get("vertex_aligner") if morphing_dict else None

        contours1_aligned, contours2_aligned = get_aligned_vertices(
            state1,
            state2,
            vertex_aligner=vertex_aligner,
            vertex_loop_mapper=vertex_loop_mapper,
        )

        # Adjust fill colors for open↔closed transitions
        fill_color1 = (
            state2.fill_color
            if not state1.closed and state2.closed
            else state1.fill_color
        )
        fill_color2 = (
            state1.fill_color
            if not state2.closed and state1.closed
            else state2.fill_color
        )

        fill_opacity1 = state1.fill_opacity if state1.closed else 0
        fill_opacity2 = state2.fill_opacity if state2.closed else 0

        # Create new states with aligned contours
        state1 = replace(
            state1,
            _aligned_contours=contours1_aligned,
            fill_color=fill_color1,
            fill_opacity=fill_opacity1,
        )
        state2 = replace(
            state2,
            _aligned_contours=contours2_aligned,
            fill_color=fill_color2,
            fill_opacity=fill_opacity2,
        )

        # Update keystates with aligned states (cached for all frames)
        self.keystates[i] = KeyState(
            state=state1, time=t1, easing=ks1.easing, morphing=ks1.morphing
        )
        self.keystates[i + 1] = KeyState(
            state=state2, time=t2, easing=ks2.easing, morphing=ks2.morphing
        )

    def _get_dynamically_aligned_states(
        self, state1: State, state2: State, segment_t: float
    ) -> Tuple[State, State]:
        """
        Get states with dynamic alignment based on current interpolated rotation.

        Only applies to rotating morphs (rotation changes during morph).
        Computes alignment fresh for each frame based on current rotation.

        Args:
            state1: Start state
            state2: End state
            segment_t: Position in segment (0.0 to 1.0)

        Returns:
            (state1, state2) with aligned contours if rotating, otherwise unchanged
        """
        # Only align if both are VertexStates and rotation changes
        if not (isinstance(state1, VertexState) and isinstance(state2, VertexState)):
            return state1, state2

        if state1.rotation == state2.rotation:
            return state1, state2  # Use static preprocessing instead

        # Compute current rotation for optimal alignment
        rotation_target = (
            state1.rotation + (state2.rotation - state1.rotation) * segment_t
        )

        # Get aligned contours for this frame's rotation
        contours1_aligned, contours2_aligned = get_aligned_vertices(
            state1, state2, rotation_target=rotation_target
        )

        # Return states with aligned contours (temporary for this frame only)
        return (
            replace(state1, _aligned_contours=contours1_aligned),
            replace(state2, _aligned_contours=contours2_aligned),
        )

    def _get_state_at_time(self, t: float) -> Tuple[Optional[State], bool]:
        """
        Get the interpolated state at a specific time.

        Returns None if t is outside the element's keystate timeline range.
        This implements the element existence model: elements only exist
        within their defined keystate timeline.

        Args:
            t: Animation time (0.0 to 1.0)

        Returns:
            Interpolated state or None if element doesn't exist at time t
        """
        if not self.keystates:
            return None, False

        # Existence check: element only exists within its keystate range
        first_time = self.keystates[0].time
        last_time = self.keystates[-1].time

        if t < first_time or t > last_time:
            return (
                None,
                False,
            )  # Element does not exist outside its defined keyframe range

        # Handle edge case: at first keystate or single keystate
        if t == first_time or len(self.keystates) == 1:
            base_state = self.keystates[0].state
            return (
                self._apply_field_timelines(base_state, t),
                False,
            )

        # Find the segment containing time t
        for i in range(len(self.keystates) - 1):
            ks1 = self.keystates[i]
            ks2 = self.keystates[i + 1]

            t1, state1 = ks1.time, ks1.state
            t2, state2 = ks2.time, ks2.state

            # ============================================================
            # STATIC PREPROCESSING (once per segment, non-rotating only)
            # ============================================================
            self._ensure_segment_preprocessed(i)

            if t1 <= t <= t2:
                # Handle coincident keystates
                if t1 == t2:
                    return (
                        self._apply_field_timelines(state2, t),
                        False,
                    )

                # Interpolate between keystates
                segment_t = (t - t1) / (t2 - t1)

                # ============================================================
                # DYNAMIC ALIGNMENT (every frame, rotating morphs only)
                # ============================================================
                state1, state2 = self._get_dynamically_aligned_states(
                    state1, state2, segment_t
                )

                # Get vertex buffer for optimized interpolation (if available)
                vertex_buffer = None
                if (
                    isinstance(state1, VertexState)
                    and isinstance(state2, VertexState)
                    and hasattr(self, "_get_vertex_buffer")
                ):
                    # Both states are VertexStates and we have buffer support
                    num_verts = (
                        len(state1._aligned_contours.outer.vertices)
                        if state1._aligned_contours
                        else 0
                    )
                    num_vertex_loops = (
                        len(state1._aligned_contours.holes)
                        if (state1._aligned_contours and state1._aligned_contours.holes)
                        else 0
                    )
                    if num_verts > 0:
                        vertex_buffer = self._get_vertex_buffer(
                            num_verts, num_vertex_loops
                        )

                interpolated_state = self.interpolation_engine.create_eased_state(
                    state1,
                    state2,
                    segment_t,
                    segment_easing_overrides=ks1.easing,
                    attribute_keystates_fields=set(self.attribute_keystates.keys()),
                    vertex_buffer=vertex_buffer,
                )

                return (
                    self._apply_field_timelines(interpolated_state, t),
                    type(state1) != type(state2)
                    and isinstance(state1, VertexState)
                    and isinstance(state2, VertexState)
                    and t != 0
                    and t != 1,
                )

        # At or past final keystate
        final_state = self.keystates[-1].state
        return self._apply_field_timelines(final_state, t), False

    def _apply_field_timelines(self, base_state: State, t: float) -> State:
        """
        Apply custom field timeline values on top of the base state.

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
            updates[field_name] = self._get_field_value_at_time(field_name, t)

        return replace(base_state, **updates)

    def _get_field_value_at_time(self, field_name: str, t: float) -> Any:
        """
        Get field value at time t from attribute_keystates.

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
