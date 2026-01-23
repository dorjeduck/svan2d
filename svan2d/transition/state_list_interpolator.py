"""Shape list interpolation for M→N morphing

Handles interpolation between lists of states using Mapper strategies.
Used for StateCollectionState and general List[State] attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from svan2d.component.state.base import State

import logging
from dataclasses import replace
from typing import Any, List, Optional

from svan2d.transition.mapping import GreedyMapper, Mapper, Match

logger = logging.getLogger(__name__)


def _normalize_to_state_list(value: Any) -> Optional[List[State]]:
    """Normalize convenience attributes to List[State]

    - None → []
    - State → [State]
    - List[State] → List[State]
    - Other → None (not a state field)
    """
    from svan2d.component.state.base import State

    if value is None:
        return []
    elif isinstance(value, State):
        return [value]
    elif isinstance(value, list) and all(isinstance(s, State) for s in value):
        return value
    else:
        return None


class StateListInterpolator:
    """Handles interpolation between lists of states (M→N morphing)"""

    def __init__(self, interpolation_engine):
        """
        Args:
            interpolation_engine: InterpolationEngine instance for recursive calls
        """
        self.engine = interpolation_engine

    def interpolate_state_list(
        self,
        start_states: List[State],
        end_states: List[State],
        eased_t: float,
        mapper: Optional[Mapper] = None,
        vertex_aligner: Optional[Any] = None,
    ) -> List[State]:
        """Interpolate between lists of states using Mapper

        Args:
            start_states: List of states at t=0
            end_states: List of states at t=1
            eased_t: Interpolation parameter
            mapper: Mapper strategy (default: GreedyMapper)
            vertex_aligner: Vertex aligner for shape morphing

        Returns:
            List of interpolated states at eased_t
        """
        if len(start_states) == 0 and len(end_states) == 0:
            return []

        if mapper is None:
            mapper = GreedyMapper()

        # Map states using position extractor
        matches: List[Match] = mapper.map(start_states, end_states, lambda s: s.pos)  # type: ignore[arg-type]

        # Process each match
        interpolated_states = []
        for match in matches:
            interpolated = self._interpolate_match(
                match, eased_t, mapper, vertex_aligner
            )
            if interpolated is not None:
                interpolated_states.append(interpolated)

        return interpolated_states

    def _interpolate_match(
        self,
        match: Match,
        eased_t: float,
        mapper: Optional[Mapper],
        vertex_aligner: Optional[Any],
    ) -> Optional[State]:
        """Interpolate a single Match

        Args:
            match: Match with start/end states
            eased_t: Interpolation parameter
            mapper: Mapper for nested state lists
            vertex_aligner: Vertex aligner for shape morphing

        Returns:
            Interpolated state, or None if should be removed
        """
        if match.is_creation:
            assert match.end is not None
            return self._interpolate_creation(match.end, eased_t)

        elif match.is_destruction:
            assert match.start is not None
            return self._interpolate_destruction(match.start, eased_t)

        else:
            assert match.start is not None and match.end is not None
            return self._interpolate_morph(
                match.start, match.end, eased_t, mapper, vertex_aligner
            )

    def _interpolate_creation(
        self, end_state: State, eased_t: float
    ) -> Optional[State]:
        """Interpolate creation: fade in at end position

        Shape stays fixed, only opacity changes from 0 to target.
        """
        if eased_t <= 0.0:
            return None

        if eased_t >= 1.0:
            return self._clean_state(end_state)

        return self._fade_state(end_state, eased_t)

    def _interpolate_destruction(
        self, start_state: State, eased_t: float
    ) -> Optional[State]:
        """Interpolate destruction: fade out at start position

        Shape stays fixed, only opacity changes from target to 0.
        """
        if eased_t >= 1.0:
            return None

        if eased_t <= 0.0:
            return self._clean_state(start_state)

        return self._fade_state(start_state, 1.0 - eased_t)

    def _interpolate_morph(
        self,
        start_state: State,
        end_state: State,
        eased_t: float,
        mapper: Optional[Mapper],
        vertex_aligner: Optional[Any],
    ) -> State:
        """Interpolate morphing between two states"""
        if eased_t <= 0.0:
            return self._clean_state(start_state)
        if eased_t >= 1.0:
            return self._clean_state(end_state)

        return self._do_interpolation(
            start_state, end_state, eased_t, mapper, vertex_aligner
        )

    def _do_interpolation(
        self,
        s1: State,
        s2: State,
        eased_t: float,
        mapper: Optional[Mapper],
        vertex_aligner: Optional[Any],
    ) -> State:
        """Perform actual interpolation between two states"""
        s1_clean = replace(
            s1, clip_state=None, mask_state=None, clip_states=None, mask_states=None
        )
        s2_clean = replace(
            s2, clip_state=None, mask_state=None, clip_states=None, mask_states=None
        )

        interpolated = self.engine.interpolate_value(
            start_state=s1_clean,
            end_state=s2_clean,
            field_name="clip_state",
            start_value=s1_clean,
            end_value=s2_clean,
            eased_t=eased_t,
            vertex_buffer=None,
            mapper=mapper,
            vertex_aligner=vertex_aligner,
        )

        return interpolated

    def _clean_state(self, state: State) -> State:
        """Clean state for final output (remove _aligned_contours)"""
        if hasattr(state, "_aligned_contours") and getattr(state, "_aligned_contours") is not None:
            return replace(state, _aligned_contours=None)
        return state

    def _fade_state(self, state: State, opacity_factor: float) -> State:
        """Scale opacity of a state by a factor (0.0-1.0)

        Used for fade in/out. Shape stays completely fixed,
        only opacity-related attributes change.
        """
        assert state.opacity is not None
        updates = {"opacity": state.opacity * opacity_factor}

        if hasattr(state, "fill_opacity") and getattr(state, "fill_opacity") is not None:
            updates["fill_opacity"] = getattr(state, "fill_opacity") * opacity_factor

        if hasattr(state, "stroke_opacity") and getattr(state, "stroke_opacity") is not None:
            updates["stroke_opacity"] = getattr(state, "stroke_opacity") * opacity_factor

        return replace(state, **updates)
