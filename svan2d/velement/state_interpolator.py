"""Core state interpolation between keystates."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple

from svan2d.component import State, VertexState
from svan2d.velement.attribute_timeline import AttributeTimelineResolver
from svan2d.velement.vertex_alignment import VertexAligner

if TYPE_CHECKING:
    from svan2d.core.point2d import Point2D, Points2D
    from svan2d.transition.easing_resolver import EasingResolver
    from svan2d.transition.interpolation_engine import InterpolationEngine
    from svan2d.velement.keystate import KeyStates

# Epsilon for floating-point time comparison to handle precision issues
TIME_EPSILON = 1e-9


def _times_equal(t1: float, t2: float) -> bool:
    """Check if two times are approximately equal within epsilon tolerance."""
    return abs(t1 - t2) < TIME_EPSILON


class StateInterpolator:
    """Handles state interpolation between keystates.

    This class encapsulates the core animation logic: finding the right
    segment for a given time and interpolating between keystates.
    """

    def __init__(
        self,
        keystates: "KeyStates",
        attribute_keystates: Dict[str, List],
        easing_resolver: "EasingResolver",
        interpolation_engine: "InterpolationEngine",
        vertex_aligner: Optional[VertexAligner] = None,
        get_vertex_buffer: Optional[
            Callable[[int, int], Tuple["Points2D", List["Points2D"]]]
        ] = None,
    ) -> None:
        """Initialize the state interpolator.

        Args:
            keystates: List of keystates for the animation
            attribute_keystates: Per-field keystate timelines
            easing_resolver: Easing resolver for field easing
            interpolation_engine: Interpolation engine for state interpolation
            vertex_aligner: Optional vertex aligner for shape morphing (VElement only)
            get_vertex_buffer: Optional vertex buffer getter for optimized interpolation
        """
        self.keystates = keystates
        self.attribute_keystates = attribute_keystates
        self.easing_resolver = easing_resolver
        self.interpolation_engine = interpolation_engine
        self.vertex_aligner = vertex_aligner
        self._get_vertex_buffer = get_vertex_buffer

        # Create timeline resolver
        self.timeline_resolver = AttributeTimelineResolver(
            attribute_keystates, keystates, easing_resolver, interpolation_engine
        )

        # Cache for pre-computed changed fields per segment
        # Key: segment_idx, Value: (changed_field_names, field_values)
        self._changed_fields_cache: Dict[int, tuple] = {}

    def get_state_at_time(self, t: float) -> Tuple[Optional[State], bool]:
        """Get the interpolated state at a specific time.

        Returns None if t is outside the element's keystate timeline range.
        This implements the element existence model: elements only exist
        within their defined keystate timeline.

        Args:
            t: Animation time (0.0 to 1.0)

        Returns:
            Tuple of (interpolated state or None, is_inbetween flag)
        """
        if not self.keystates:
            return None, False

        # Existence check: element only exists within its keystate range
        first_time = self.keystates[0].time
        last_time = self.keystates[-1].time
        assert first_time is not None and last_time is not None

        if t < first_time - TIME_EPSILON or t > last_time + TIME_EPSILON:
            return None, False

        # Handle edge case: at first keystate or single keystate
        if _times_equal(t, first_time) or len(self.keystates) == 1:
            ks = self.keystates[0]
            if ks.render_index is None:
                return None, False  # Don't render
            if ks.render_index == 1:
                assert (
                    ks.outgoing_state is not None
                )  # Guaranteed by KeyState validation
                base_state = ks.outgoing_state
            else:
                base_state = ks.state
            return self.timeline_resolver.apply_field_timelines(base_state, t), False

        # Find the segment containing time t using binary search
        num_keystates = len(self.keystates)

        lo, hi = 0, num_keystates - 1
        segment_idx = None
        while lo < hi:
            mid = (lo + hi) // 2
            mid_time = self.keystates[mid].time
            assert mid_time is not None
            if mid_time <= t:
                if mid == num_keystates - 1:
                    segment_idx = mid
                    break
                next_time = self.keystates[mid + 1].time
                assert next_time is not None
                if next_time >= t:
                    segment_idx = mid
                    break
                lo = mid + 1
            else:
                hi = mid

        if segment_idx is None:
            segment_idx = lo

        # Check if t exactly matches a keystate at segment boundaries
        # Important for dual-state keystates: render based on render_index
        for idx in (segment_idx, segment_idx + 1):
            if idx >= num_keystates:
                continue
            ks = self.keystates[idx]
            if ks.time is not None and _times_equal(ks.time, t):
                if ks.render_index is None:
                    return None, False  # Don't render
                if ks.render_index == 1:
                    assert (
                        ks.outgoing_state is not None
                    )  # Guaranteed by KeyState validation
                    rendered_state = ks.outgoing_state
                else:
                    rendered_state = ks.state
                return (
                    self.timeline_resolver.apply_field_timelines(rendered_state, t),
                    False,
                )

        # Process only the found segment
        for i in [segment_idx] if segment_idx < num_keystates - 1 else []:
            ks1 = self.keystates[i]
            ks2 = self.keystates[i + 1]

            t1 = ks1.time
            t2 = ks2.time
            # Use outgoing_state for segment source if available
            state1 = ks1.outgoing_state or ks1.state
            state2 = ks2.state
            assert t1 is not None and t2 is not None

            # Static preprocessing for vertex alignment (if aligner provided)
            if self.vertex_aligner:

                self.vertex_aligner.ensure_segment_preprocessed(self.keystates, i)
                # Refresh states after potential preprocessing
                state1 = self.keystates[i].outgoing_state or self.keystates[i].state
                state2 = self.keystates[i + 1].state

            if t1 <= t <= t2:
                # Handle coincident keystates
                if _times_equal(t1, t2):
                    return (
                        self.timeline_resolver.apply_field_timelines(state2, t),
                        False,
                    )

                # Interpolate between keystates
                segment_t = (t - t1) / (t2 - t1)

                # Dynamic alignment for rotating morphs (if aligner provided)
                if self.vertex_aligner:
                    state1, state2 = self.vertex_aligner.get_dynamically_aligned_states(
                        state1, state2, segment_t
                    )

                # Get vertex buffer for optimized interpolation (if available)
                vertex_buffer = None
                if (
                    isinstance(state1, VertexState)
                    and isinstance(state2, VertexState)
                    and self._get_vertex_buffer is not None
                ):
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

                # Get or compute changed fields for this segment (lazy field interpolation)
                attr_fields = set(self.attribute_keystates.keys())
                if i not in self._changed_fields_cache:
                    from svan2d.transition.interpolation_engine import (
                        InterpolationEngine,
                    )

                    self._changed_fields_cache[i] = (
                        InterpolationEngine.compute_changed_fields(
                            state1, state2, attr_fields
                        )
                    )
                changed_fields = self._changed_fields_cache[i]

                interpolated_state = self.interpolation_engine.create_eased_state(
                    state1,
                    state2,
                    segment_t,
                    segment_easing_overrides=(
                        ks1.transition_config.easing_dict
                        if ks1.transition_config
                        else None
                    ),
                    attribute_keystates_fields=attr_fields,
                    vertex_buffer=vertex_buffer,
                    segment_interpolation_config=(
                        ks1.transition_config.interpolation_dict
                        if ks1.transition_config
                        else None
                    ),
                    morphing_config=(
                        ks1.transition_config.morphing_config
                        if ks1.transition_config
                        else None
                    ),
                    changed_fields=changed_fields,
                    linear_angle_interpolation=(
                        ks1.transition_config.linear_angle_interpolation
                        if ks1.transition_config
                        else False
                    ),
                )

                # Determine if this is an "inbetween" frame (different state types morphing)
                is_inbetween = (
                    type(state1) != type(state2)
                    and isinstance(state1, VertexState)
                    and isinstance(state2, VertexState)
                    and t != 0
                    and t != 1
                )

                return (
                    self.timeline_resolver.apply_field_timelines(interpolated_state, t),
                    is_inbetween,
                )

        # At or past final keystate
        final_ks = self.keystates[-1]
        if final_ks.render_index is None:
            return None, False  # Don't render
        if final_ks.render_index == 1:
            assert (
                final_ks.outgoing_state is not None
            )  # Guaranteed by KeyState validation
            final_state = final_ks.outgoing_state
        else:
            final_state = final_ks.state
        return self.timeline_resolver.apply_field_timelines(final_state, t), False
