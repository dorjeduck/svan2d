"""Vertex alignment for shape morphing."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Tuple

from svan2d.component import State, VertexState
from svan2d.transition.align_vertices import get_aligned_vertices
from svan2d.velement.keystate import KeyState

if TYPE_CHECKING:
    from svan2d.velement.keystate import KeyStates
    from svan2d.velement.morphing import MorphingConfig


class VertexAligner:
    """Handles vertex alignment for shape morphing.

    Only used by VElement, not VElementGroup (groups don't morph).
    """

    def ensure_segment_preprocessed(self, keystates: "KeyStates", i: int) -> None:
        """Ensure segment i→(i+1) has static alignment preprocessing applied.

        Only runs for non-rotating morphs (rotation doesn't change).
        Stores aligned contours in keystates for reuse across all frames.

        Args:
            keystates: List of keystates (will be mutated)
            i: Segment index (processes keystates[i] and keystates[i+1])
        """
        ks1 = keystates[i]
        ks2 = keystates[i + 1]

        state1, state2 = ks1.state, ks2.state
        t1, t2 = ks1.time, ks2.time

        # Check if preprocessing needed
        if not (
            isinstance(state1, VertexState)
            and isinstance(state2, VertexState)
            and state2._aligned_contours is None
            and state1.need_morph(state2)
        ):
            return  # Already preprocessed or not a vertex morph

        # Extract morphing config (prefer ks2's config)
        from svan2d.velement.morphing import MorphingConfig

        morphing_config = (
            ks2.transition_config.morphing_config
            if ks2.transition_config
            else (
                ks1.transition_config.morphing_config if ks1.transition_config else None
            )
        )

        if isinstance(morphing_config, MorphingConfig):
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
        mapper = morphing_dict.get("mapper") if morphing_dict else None
        vertex_aligner = morphing_dict.get("vertex_aligner") if morphing_dict else None

        contours1_aligned, contours2_aligned = get_aligned_vertices(
            state1,
            state2,
            vertex_aligner=vertex_aligner,
            mapper=mapper,
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
        keystates[i] = KeyState(
            state=state1,
            time=t1,
            transition_config=ks1.transition_config,
        )
        keystates[i + 1] = KeyState(
            state=state2,
            time=t2,
            transition_config=ks2.transition_config,
        )

    def get_dynamically_aligned_states(
        self, state1: State, state2: State, segment_t: float
    ) -> Tuple[State, State]:
        """Get states with dynamic alignment based on current interpolated rotation.

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
        assert state1.rotation is not None and state2.rotation is not None
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
