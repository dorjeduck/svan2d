"""Shared builder mixin for VElement and VElementGroup."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from svan2d.component.state.base import State
from svan2d.velement.keystate import KeyState
from svan2d.velement.keystate_parser import (
    AttributeKeyStatesDict,
    parse_attribute_keystates,
    parse_element_keystates,
)
from svan2d.velement.transition import CurveFunction, EasingFunction, TransitionConfig

if TYPE_CHECKING:
    from svan2d.velement.morphing import MorphingConfig

T = TypeVar("T", bound="KeystateBuilder")

# Type alias for keystate tuple
KeystateTuple = Tuple[
    State, Optional[State], Optional[float], Optional[TransitionConfig], int | None
]


@dataclass(frozen=True)
class BuilderState:
    """Internal state for chainable builder methods (immutable)."""

    # Tuple: (state, outgoing_state, time, transition_config, render_index)
    keystates: Tuple[KeystateTuple, ...] = field(default_factory=tuple)
    pending_transition: Optional[TransitionConfig] = None
    default_transition: Optional[TransitionConfig] = None
    interpolation_dict: Optional[Dict[str, Any]] = None

    def with_keystate(self, keystate: KeystateTuple) -> "BuilderState":
        """Return new BuilderState with keystate added."""
        return BuilderState(
            keystates=self.keystates + (keystate,),
            pending_transition=None,  # Reset pending after adding keystate
            default_transition=self.default_transition,
            interpolation_dict=self.interpolation_dict,
        )

    def with_pending_transition(self, transition: TransitionConfig) -> "BuilderState":
        """Return new BuilderState with pending transition set."""
        return BuilderState(
            keystates=self.keystates,
            pending_transition=transition,
            default_transition=self.default_transition,
            interpolation_dict=self.interpolation_dict,
        )

    def with_default_transition(self, transition: TransitionConfig) -> "BuilderState":
        """Return new BuilderState with default transition set."""
        return BuilderState(
            keystates=self.keystates,
            pending_transition=self.pending_transition,
            default_transition=transition,
            interpolation_dict=self.interpolation_dict,
        )

    def with_interpolation_dict(
        self, interpolation_dict: Dict[str, Any]
    ) -> "BuilderState":
        """Return new BuilderState with interpolation_dict set."""
        return BuilderState(
            keystates=self.keystates,
            pending_transition=self.pending_transition,
            default_transition=self.default_transition,
            interpolation_dict=interpolation_dict,
        )

    def with_last_keystate_updated(
        self, transition: Optional[TransitionConfig]
    ) -> "BuilderState":
        """Return new BuilderState with last keystate's transition updated."""
        if not self.keystates:
            return self

        prev_state, prev_outgoing, prev_time, _, prev_render_index = self.keystates[-1]
        updated_keystate = (
            prev_state,
            prev_outgoing,
            prev_time,
            transition,
            prev_render_index,
        )
        return BuilderState(
            keystates=self.keystates[:-1] + (updated_keystate,),
            pending_transition=None,
            default_transition=self.default_transition,
            interpolation_dict=self.interpolation_dict,
        )


class KeystateBuilder:
    """Mixin providing chainable builder methods for animation construction.

    Subclasses must:
    - Initialize self._builder = BuilderState() in __init__
    - Initialize self._attribute_easing = None in __init__
    - Initialize self._attribute_keystates = None in __init__
    - Implement _replace_builder() to return new instance with updated builder
    - Call _finalize_build() to convert builder state to final keystates
    """

    _builder: Optional[BuilderState]
    _attribute_easing: Optional[Dict[str, EasingFunction]]
    _attribute_keystates: Optional[AttributeKeyStatesDict]

    @abstractmethod
    def _replace_builder(self: T, new_builder: BuilderState) -> T:
        """Return a new instance with the updated builder state.

        Subclasses must implement this to create a copy with the new builder.
        """
        ...

    @abstractmethod
    def _replace_attributes(
        self: T,
        new_builder: BuilderState,
        new_easing: Optional[Dict[str, EasingFunction]],
        new_keystates: Optional[AttributeKeyStatesDict],
    ) -> T:
        """Return a new instance with updated builder and attribute settings.

        Subclasses must implement this to create a copy with the new settings.
        """
        ...

    def keystate(
        self: T,
        state: State | list[State],
        at: float | None = None,
        render_index: int | None = 0,
    ) -> T:
        """Add a keystate at the specified time.

        Args:
            state: State for this keystate, or a 2-element list [incoming_state, outgoing_state]
                   for dual-state keystates. When using dual-state:
                   - state[0]: interpolation target coming IN
                   - state[1]: interpolation source going OUT
            at: Time position (0.0-1.0), or None for auto-timing
            render_index: Which state to render at exactly this time (0 or 1, default 0).
                          Only applicable for dual-state keystates.

        Returns:
            New instance with keystate added
        """
        if self._builder is None:
            raise RuntimeError("Cannot modify element after rendering has begun.")

        # Parse dual-state format
        incoming_state: State
        outgoing_state: State | None = None

        if isinstance(state, list):
            if len(state) != 2:
                raise ValueError(
                    f"Dual-state keystate requires exactly 2 states, got {len(state)}"
                )
            if not isinstance(state[0], State) or not isinstance(state[1], State):
                raise TypeError(
                    "Both elements of dual-state list must be State instances"
                )
            incoming_state = state[0]
            outgoing_state = state[1]
        else:
            incoming_state = state
            if render_index not in (0, None):
                raise ValueError(
                    "render_index=1 can only be used with dual-state keystates"
                )

        # Build new builder state
        new_builder = self._builder

        # Attach transition to previous keystate (explicit or default)
        if len(new_builder.keystates) > 0:
            transition_to_apply = (
                new_builder.pending_transition or new_builder.default_transition
            )

            if transition_to_apply is not None:
                new_builder = new_builder.with_last_keystate_updated(
                    transition_to_apply
                )

        # Add new keystate
        new_keystate: KeystateTuple = (
            incoming_state,
            outgoing_state,
            at,
            None,
            render_index,
        )
        new_builder = new_builder.with_keystate(new_keystate)

        return self._replace_builder(new_builder)

    def keystates(
        self: T,
        states: Sequence[State],
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
            New instance with keystates added
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

        # Chain immutably
        result = self

        # Extend with first state at 0.0 if needed
        if extend and start > 0.0:
            result = result.keystate(states[0], at=0.0)

        # Add keystates at calculated times
        for state, t in zip(states, times):
            result = result.keystate(state, at=t)

        # Extend with last state at 1.0 if needed
        if extend and end < 1.0:
            result = result.keystate(states[-1], at=1.0)

        return result

    def transition(
        self: T,
        easing_dict: Optional[Dict[str, EasingFunction]] = None,
        interpolation_dict: Optional[Dict[str, Any]] = None,
        morphing_config: Optional["MorphingConfig"] = None,
        linear_angle_interpolation: bool = False,
        state_interpolation: Optional[Callable] = None,
    ) -> T:
        """Configure the transition between the previous and next keystate.

        Multiple consecutive transition() calls merge their configurations.

        Args:
            easing_dict: Per-field easing functions for this segment
            interpolation_dict: Per-field interpolation functions {field_name: func}
                              - Point2D: (p1, p2, t) -> Point2D
                              - Rotation: (r1, r2, t) -> float
            morphing_config: Morphing configuration for vertex state transitions
            linear_angle_interpolation: If True, rotation interpolates linearly without angle wrapping
            state_interpolation: Optional callable (start_state, end_state, t) -> State that
                                bypasses all per-field interpolation. t is raw segment t (0→1).

        Returns:
            New instance with transition configured
        """
        if self._builder is None:
            raise RuntimeError("Cannot modify element after rendering has begun.")

        if len(self._builder.keystates) == 0:
            raise ValueError("transition() cannot be called before the first keystate")

        # Merge with pending transition if exists
        if self._builder.pending_transition is None:
            new_transition = TransitionConfig(
                easing_dict=easing_dict,
                interpolation_dict=interpolation_dict,
                morphing_config=morphing_config,
                linear_angle_interpolation=linear_angle_interpolation,
                state_interpolation=state_interpolation,
            )
        else:
            merged_easing = self._builder.pending_transition.easing_dict or {}
            if easing_dict:
                merged_easing = {**merged_easing, **easing_dict}

            merged_path = self._builder.pending_transition.interpolation_dict or {}
            if interpolation_dict:
                merged_path = {**merged_path, **interpolation_dict}

            merged_morphing = (
                morphing_config
                if morphing_config is not None
                else self._builder.pending_transition.morphing_config
            )

            # linear_angle_interpolation: new call overrides pending
            merged_linear_angle_interpolation = (
                linear_angle_interpolation
                if linear_angle_interpolation
                else self._builder.pending_transition.linear_angle_interpolation
            )

            # state_interpolation: new call overrides pending
            merged_state_interpolation = (
                state_interpolation
                if state_interpolation is not None
                else self._builder.pending_transition.state_interpolation
            )

            new_transition = TransitionConfig(
                easing_dict=merged_easing if merged_easing else None,
                interpolation_dict=merged_path if merged_path else None,
                morphing_config=merged_morphing,
                linear_angle_interpolation=merged_linear_angle_interpolation,
                state_interpolation=merged_state_interpolation,
            )

        new_builder = self._builder.with_pending_transition(new_transition)
        return self._replace_builder(new_builder)

    def default_transition(
        self: T,
        easing_dict: Optional[Dict[str, EasingFunction]] = None,
        interpolation_dict: Optional[Dict[str, Any]] = None,
        morphing: Optional["MorphingConfig"] = None,
        state_interpolation: Optional[Callable] = None,
    ) -> T:
        """Set default transition parameters for all subsequent segments.

        Args:
            easing_dict: Per-field easing functions to use as default
            interpolation_dict: Per-field path functions to use as default
            morphing: Morphing configuration to use as default
            state_interpolation: Optional callable (start_state, end_state, t) -> State that
                                bypasses all per-field interpolation. t is raw segment t (0→1).

        Returns:
            New instance with default transition set
        """
        if self._builder is None:
            raise RuntimeError("Cannot modify element after rendering has begun.")

        if self._builder.default_transition is None:
            new_default = TransitionConfig(
                easing_dict=easing_dict,
                interpolation_dict=interpolation_dict,
                morphing_config=morphing,
                state_interpolation=state_interpolation,
            )
        else:
            merged_easing = self._builder.default_transition.easing_dict or {}
            if easing_dict:
                merged_easing = {**merged_easing, **easing_dict}

            merged_path = self._builder.default_transition.interpolation_dict or {}
            if interpolation_dict:
                merged_path = {**merged_path, **interpolation_dict}

            merged_morphing = (
                morphing
                if morphing is not None
                else self._builder.default_transition.morphing_config
            )

            # state_interpolation: new call overrides pending
            merged_state_interpolation = (
                state_interpolation
                if state_interpolation is not None
                else self._builder.default_transition.state_interpolation
            )

            new_default = TransitionConfig(
                easing_dict=merged_easing if merged_easing else None,
                interpolation_dict=merged_path if merged_path else None,
                morphing_config=merged_morphing,
                state_interpolation=merged_state_interpolation,
            )

        new_builder = self._builder.with_default_transition(new_default)
        return self._replace_builder(new_builder)

    def attributes(
        self: T,
        easing_dict: Optional[Dict[str, EasingFunction]] = None,
        interpolation_dict: Optional[Dict[str, Any]] = None,
        keystates_dict: Optional[AttributeKeyStatesDict] = None,
    ) -> T:
        """Set element-level attribute configuration.

        Args:
            easing_dict: Per-field easing functions {field_name: easing_func}
            interpolation_dict: Per-field path functions {field_name: path_func}
            keystates_dict: Per-field keystate timelines {field_name: [values]}

        Returns:
            New instance with attributes set
        """
        if self._builder is None:
            raise RuntimeError("Cannot modify element after rendering has begun.")

        new_builder = self._builder
        new_easing = self._attribute_easing
        new_keystates = self._attribute_keystates

        if easing_dict is not None:
            new_easing = easing_dict
        if interpolation_dict is not None:
            new_builder = new_builder.with_interpolation_dict(interpolation_dict)
        if keystates_dict is not None:
            new_keystates = keystates_dict

        return self._replace_attributes(new_builder, new_easing, new_keystates)

    def _merge_element_path_into_transition(
        self, transition_config: Optional[TransitionConfig]
    ) -> Optional[TransitionConfig]:
        """Merge element-level path config into segment transition."""
        if self._builder is None or self._builder.interpolation_dict is None:
            return transition_config

        if transition_config is None:
            return TransitionConfig(interpolation_dict=self._builder.interpolation_dict)

        # Segment path takes precedence, element path fills gaps
        segment_path = transition_config.interpolation_dict or {}
        merged_path = {**self._builder.interpolation_dict, **segment_path}

        return TransitionConfig(
            easing_dict=transition_config.easing_dict,
            morphing_config=transition_config.morphing_config,
            interpolation_dict=merged_path if merged_path else None,
            linear_angle_interpolation=transition_config.linear_angle_interpolation,
            state_interpolation=transition_config.state_interpolation,
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

        # Validate compatible state types (ShapeCollectionState cannot mix with others)
        from svan2d.component.state.state_collection import StateCollectionState

        for i in range(len(self._builder.keystates) - 1):
            state1 = self._builder.keystates[i][0]
            state2 = self._builder.keystates[i + 1][0]
            is_collection1 = isinstance(state1, StateCollectionState)
            is_collection2 = isinstance(state2, StateCollectionState)

            if is_collection1 != is_collection2:
                type1 = type(state1).__name__
                type2 = type(state2).__name__
                raise ValueError(
                    f"Cannot chain {type1} with {type2}. "
                    f"ShapeCollectionState must be in a separate VElement. "
                    f"Use adjacent time ranges (e.g., individual shapes at=0.0-0.4, "
                    f"collection at=0.4-0.7) in separate VElements."
                )

        # Check for orphan transition after last keystate
        if self._builder.pending_transition is not None:
            raise ValueError(
                "transition() after the last keystate has no effect. "
                "Remove the trailing transition() call."
            )

        # Check for duplicate keystate times
        times = [ks[2] for ks in self._builder.keystates if ks[2] is not None]
        seen = set()
        for t in times:
            # if t in seen:
            #    raise ValueError(f"Duplicate keystate time {t} detected.")
            seen.add(t)

        # Auto-expand: single keystate with implicit time → duplicate to span [0, 1].
        # VElement(state=s) should persist across entire timeline, not just t=0.
        # Explicit at= is preserved (user intentionally pinned to one time point).
        if len(self._builder.keystates) == 1 and self._builder.keystates[0][2] is None:
            ks = self._builder.keystates[0]
            self._builder = BuilderState(
                keystates=(ks, ks),
                pending_transition=self._builder.pending_transition,
                default_transition=self._builder.default_transition,
                interpolation_dict=self._builder.interpolation_dict,
            )

        # Convert internal keystates to KeyState objects
        keystates: List[KeyState] = []
        for (
            state,
            outgoing_state,
            time,
            transition_config,
            render_index,
        ) in self._builder.keystates:
            effective_transition = self._merge_element_path_into_transition(
                transition_config
            )
            keystates.append(
                KeyState(
                    state=state,
                    time=time,
                    transition_config=effective_transition,
                    outgoing_state=outgoing_state,
                    render_index=render_index,
                )
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

        return parse_element_keystates(keystates), attribute_keystates  # type: ignore[arg-type]
