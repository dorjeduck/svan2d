"""Core state interpolation between keystates."""

from __future__ import annotations
from typing import Optional, Tuple, Dict, List, Callable, TYPE_CHECKING

from svan2d.component import VertexState, State
from svan2d.velement.attribute_timeline import AttributeTimelineResolver
from svan2d.velement.vertex_alignment import VertexAligner

if TYPE_CHECKING:
    from svan2d.velement.keystate import KeyStates
    from svan2d.transition.easing_resolver import EasingResolver
    from svan2d.transition.interpolation_engine import InterpolationEngine
    from svan2d.core.point2d import Point2D, Points2D


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

        if t < first_time or t > last_time:
            return None, False

        # Check skip_render_at flag for keystates at exactly time t
        for ks in self.keystates:
            if ks.time == t and ks.skip_render_at:
                return None, False

        # Handle edge case: at first keystate or single keystate
        if t == first_time or len(self.keystates) == 1:
            base_state = self.keystates[0].state
            return self.timeline_resolver.apply_field_timelines(base_state, t), False

        # Find the segment containing time t
        for i in range(len(self.keystates) - 1):
            ks1 = self.keystates[i]
            ks2 = self.keystates[i + 1]

            t1, state1 = ks1.time, ks1.state
            t2, state2 = ks2.time, ks2.state

            # Static preprocessing for vertex alignment (if aligner provided)
            if self.vertex_aligner:
                self.vertex_aligner.ensure_segment_preprocessed(self.keystates, i)
                # Refresh states after potential preprocessing
                state1 = self.keystates[i].state
                state2 = self.keystates[i + 1].state

            if t1 <= t <= t2:
                # Handle coincident keystates
                if t1 == t2:
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

                interpolated_state = self.interpolation_engine.create_eased_state(
                    state1,
                    state2,
                    segment_t,
                    segment_easing_overrides=(
                        ks1.transition_config.easing_dict
                        if ks1.transition_config
                        else None
                    ),
                    attribute_keystates_fields=set(self.attribute_keystates.keys()),
                    vertex_buffer=vertex_buffer,
                    segment_path_config=(
                        ks1.transition_config.curve_dict
                        if ks1.transition_config
                        else None
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
        final_state = self.keystates[-1].state
        return self.timeline_resolver.apply_field_timelines(final_state, t), False
