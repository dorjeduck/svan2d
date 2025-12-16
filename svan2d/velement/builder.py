"""Shared builder mixin for VElement and VElementGroup."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Callable, Dict, TypeVar, TYPE_CHECKING

from svan2d.component import State
from svan2d.velement.transition import TransitionConfig, CurveFunction
from svan2d.velement.keystate import KeyState
from svan2d.velement.keystate_parser import (
    AttributeKeyStatesDict,
    parse_element_keystates,
    parse_attribute_keystates,
)

if TYPE_CHECKING:
    from svan2d.velement.morphing import Morphing

T = TypeVar("T", bound="KeystateBuilder")


@dataclass
class BuilderState:
    """Internal state for chainable builder methods."""

    keystates: List[Tuple[State, Optional[float], Optional[TransitionConfig]]] = field(
        default_factory=list
    )
    pending_transition: Optional[TransitionConfig] = None
    default_transition: Optional[TransitionConfig] = None
    curve_dict: Optional[Dict[str, CurveFunction]] = None


class KeystateBuilder:
    """Mixin providing chainable builder methods for animation construction.

    Subclasses must:
    - Initialize self._builder = BuilderState() in __init__
    - Initialize self._attribute_easing = None in __init__
    - Initialize self._attribute_keystates = None in __init__
    - Call _finalize_build() to convert builder state to final keystates
    """

    _builder: Optional[BuilderState]
    _attribute_easing: Optional[Dict[str, Callable[[float], float]]]
    _attribute_keystates: Optional[AttributeKeyStatesDict]

    def keystate(self: T, state: State, at: Optional[float] = None) -> T:
        """Add a keystate at the specified time.

        Args:
            state: State for this keystate
            at: Time position (0.0-1.0), or None for auto-timing

        Returns:
            self for chaining
        """
        if self._builder is None:
            raise RuntimeError("Cannot modify element after rendering has begun.")

        # Attach transition to previous keystate (explicit or default)
        if len(self._builder.keystates) > 0:
            prev_state, prev_time, _ = self._builder.keystates[-1]

            transition_to_apply = (
                self._builder.pending_transition or self._builder.default_transition
            )

            if transition_to_apply is not None:
                self._builder.keystates[-1] = (
                    prev_state,
                    prev_time,
                    transition_to_apply,
                )

            self._builder.pending_transition = None

        # Add new keystate
        self._builder.keystates.append((state, at, None))
        return self

    def keystates(
        self: T,
        states: List[State],
        between: Optional[List[float]] = None,
        extend: bool = False,
        at: Optional[List[float]] = None,
    ) -> T:
        """Add multiple keystates with automatic timing.

        Args:
            states: List of states to add
            between: Time range [start, end] for the states (default [0.0, 1.0])
            extend: If True and time range doesn't cover [0,1], extend with
                    copies of first/last state at 0.0/1.0
            at: Exact times for each state (overrides between if both given)

        Returns:
            self for chaining
        """
        if not states:
            return self

        # Determine times for each state
        if at is not None:
            if len(at) != len(states):
                raise ValueError(
                    f"Length of 'at' ({len(at)}) must match length of 'states' ({len(states)})"
                )
            times = at
            start, end = times[0], times[-1]
        else:
            start, end = between if between else [0.0, 1.0]
            n = len(states)
            if n == 1:
                times = [start]
            else:
                times = [start + (end - start) * i / (n - 1) for i in range(n)]

        # Extend with first state at 0.0 if needed
        if extend and start > 0.0:
            self.keystate(states[0], at=0.0)

        # Add keystates at calculated times
        for state, t in zip(states, times):
            self.keystate(state, at=t)

        # Extend with last state at 1.0 if needed
        if extend and end < 1.0:
            self.keystate(states[-1], at=1.0)

        return self

    def transition(
        self: T,
        easing_dict: Optional[Dict[str, Callable[[float], float]]] = None,
        curve_dict: Optional[Dict[str, CurveFunction]] = None,
        morphing: Optional["Morphing"] = None,
    ) -> T:
        """Configure the transition between the previous and next keystate.

        Multiple consecutive transition() calls merge their configurations.

        Args:
            easing_dict: Per-field easing functions for this segment
            curve_dict: Per-field path functions for this segment
            morphing: Morphing configuration for vertex state transitions

        Returns:
            self for chaining
        """
        if self._builder is None:
            raise RuntimeError("Cannot modify element after rendering has begun.")

        if len(self._builder.keystates) == 0:
            raise ValueError("transition() cannot be called before the first keystate")

        # Merge with pending transition if exists
        if self._builder.pending_transition is None:
            self._builder.pending_transition = TransitionConfig(
                easing_dict=easing_dict, curve_dict=curve_dict, morphing=morphing
            )
        else:
            merged_easing = self._builder.pending_transition.easing_dict or {}
            if easing_dict:
                merged_easing = {**merged_easing, **easing_dict}

            merged_path = self._builder.pending_transition.curve_dict or {}
            if curve_dict:
                merged_path = {**merged_path, **curve_dict}

            merged_morphing = (
                morphing
                if morphing is not None
                else self._builder.pending_transition.morphing
            )

            self._builder.pending_transition = TransitionConfig(
                easing_dict=merged_easing if merged_easing else None,
                curve_dict=merged_path if merged_path else None,
                morphing=merged_morphing,
            )
        return self

    def default_transition(
        self: T,
        easing_dict: Optional[Dict[str, Callable[[float], float]]] = None,
        curve_dict: Optional[Dict[str, CurveFunction]] = None,
        morphing: Optional["Morphing"] = None,
    ) -> T:
        """Set default transition parameters for all subsequent segments.

        Args:
            easing_dict: Per-field easing functions to use as default
            curve_dict: Per-field path functions to use as default
            morphing: Morphing configuration to use as default

        Returns:
            self for chaining
        """
        if self._builder is None:
            raise RuntimeError("Cannot modify element after rendering has begun.")

        if self._builder.default_transition is None:
            self._builder.default_transition = TransitionConfig(
                easing_dict=easing_dict, curve_dict=curve_dict, morphing=morphing
            )
        else:
            merged_easing = self._builder.default_transition.easing_dict or {}
            if easing_dict:
                merged_easing = {**merged_easing, **easing_dict}

            merged_path = self._builder.default_transition.curve_dict or {}
            if curve_dict:
                merged_path = {**merged_path, **curve_dict}

            merged_morphing = (
                morphing
                if morphing is not None
                else self._builder.default_transition.morphing
            )

            self._builder.default_transition = TransitionConfig(
                easing_dict=merged_easing if merged_easing else None,
                curve_dict=merged_path if merged_path else None,
                morphing=merged_morphing,
            )
        return self

    def attributes(
        self: T,
        easing_dict: Optional[Dict[str, Callable[[float], float]]] = None,
        curve_dict: Optional[Dict[str, CurveFunction]] = None,
        keystates_dict: Optional[AttributeKeyStatesDict] = None,
    ) -> T:
        """Set element-level attribute configuration.

        Args:
            easing_dict: Per-field easing functions {field_name: easing_func}
            curve_dict: Per-field path functions {field_name: path_func}
            keystates_dict: Per-field keystate timelines {field_name: [values]}

        Returns:
            self for chaining
        """
        if easing_dict is not None:
            self._attribute_easing = easing_dict
        if curve_dict is not None:
            if self._builder is None:
                raise RuntimeError("Cannot modify element after rendering has begun.")
            self._builder.curve_dict = curve_dict
        if keystates_dict is not None:
            self._attribute_keystates = keystates_dict
        return self

    def _merge_element_path_into_transition(
        self, transition_config: Optional[TransitionConfig]
    ) -> Optional[TransitionConfig]:
        """Merge element-level path config into segment transition."""
        if self._builder is None or self._builder.curve_dict is None:
            return transition_config

        if transition_config is None:
            return TransitionConfig(curve_dict=self._builder.curve_dict)

        # Segment path takes precedence, element path fills gaps
        segment_path = transition_config.curve_dict or {}
        merged_path = {**self._builder.curve_dict, **segment_path}

        return TransitionConfig(
            easing_dict=transition_config.easing_dict,
            morphing=transition_config.morphing,
            curve_dict=merged_path if merged_path else None,
        )

    def _finalize_build(self) -> Tuple[List[KeyState], Dict]:
        """Convert builder state to final keystates and attribute_keystates.

        Returns:
            Tuple of (keystates list, attribute_keystates dict)

        Raises:
            ValueError: If no keystates or orphan transition
        """
        if self._builder is None:
            raise RuntimeError("Builder already finalized.")

        # Validate minimum keystates
        if len(self._builder.keystates) < 1:
            raise ValueError(
                "Element requires at least 1 keystate. Use .keystate() to add states."
            )

        # Check for orphan transition after last keystate
        if self._builder.pending_transition is not None:
            raise ValueError(
                "transition() after the last keystate has no effect. "
                "Remove the trailing transition() call."
            )

        # Convert internal keystates to KeyState objects
        keystates: List[KeyState] = []
        for state, time, transition_config in self._builder.keystates:
            effective_transition = self._merge_element_path_into_transition(
                transition_config
            )
            keystates.append(
                KeyState(state=state, time=time, transition_config=effective_transition)
            )

        # Parse attribute keystates
        attribute_keystates = {}
        if self._attribute_keystates:
            for field_name, timeline in self._attribute_keystates.items():
                if not timeline:
                    raise ValueError(f"Empty timeline for field '{field_name}'")
                attribute_keystates[field_name] = parse_attribute_keystates(timeline)

        # Clear builder state
        self._builder = None

        return parse_element_keystates(keystates), attribute_keystates
