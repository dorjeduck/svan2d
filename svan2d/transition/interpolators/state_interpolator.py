"""Interpolator for State objects (recursive state interpolation)."""

from dataclasses import replace
from typing import Any, Optional

from svan2d.component.state.base import State


class StateInterpolator:
    """Handles interpolation between State objects."""

    def __init__(self, engine: Any):
        """
        Initialize with reference to the interpolation engine.

        Args:
            engine: InterpolationEngine instance for recursive calls
        """
        self._engine = engine

    def interpolate(
        self,
        start_value: State,
        end_value: State,
        eased_t: float,
        mapper: Optional[Any] = None,
        vertex_aligner: Optional[Any] = None,
    ) -> State:
        """
        Interpolate between two State objects.

        Handles morph detection for VertexState subclasses and recursively
        interpolates all state fields.

        Args:
            start_value: Starting state
            end_value: Ending state
            eased_t: Eased interpolation parameter (0.0 to 1.0)
            mapper: Optional mapper for M→N matching
            vertex_aligner: Optional vertex aligner for shape morphing

        Returns:
            Interpolated state
        """
        # Check if this is a morph between different VertexState types
        from svan2d.component.state.base_vertex import VertexState

        start_state = start_value
        end_state = end_value

        if (
            isinstance(start_value, VertexState)
            and isinstance(end_value, VertexState)
            and start_value.need_morph(end_value)
        ):
            # Need to align vertices for morphing
            from svan2d.transition.align_vertices import get_aligned_vertices

            contours1_aligned, contours2_aligned = get_aligned_vertices(
                start_value,
                end_value,
                vertex_aligner=vertex_aligner,
                mapper=mapper,
            )

            start_state = replace(start_value, _aligned_contours=contours1_aligned)
            end_state = replace(end_value, _aligned_contours=contours2_aligned)

        # Re-wrap mapper/aligner for recursive call
        morphing_config = None
        if mapper is not None or vertex_aligner is not None:
            from svan2d.velement.morphing import MorphingConfig

            morphing_config = MorphingConfig(
                mapper=mapper, vertex_aligner=vertex_aligner
            )

        # Recursively interpolate the state
        return self._engine.create_eased_state(
            start_state,
            end_state,
            eased_t,
            segment_easing_overrides=None,
            attribute_keystates_fields=set(),
            vertex_buffer=None,
            segment_path_config=None,
            morphing_config=morphing_config,
        )
