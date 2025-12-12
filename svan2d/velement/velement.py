"""Element class - the central object that combines renderers and states"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Callable, List, Tuple

import drawsvg as dw

from svan2d.component import Renderer, State, get_renderer_instance_for_state
from svan2d.velement.base_velement import BaseVElement
from svan2d.component.renderer.base_vertex import VertexRenderer
from svan2d.velement.keystate_parser import AttributeKeyStatesConfig
from svan2d.core.point2d import Point2D, Points2D
from svan2d.velement.transition import TransitionConfig, PathFunction
from svan2d.velement.keystate import KeyState
from svan2d.velement.morphing import Morphing


@dataclass
class BuilderState:
    """Internal state for VElement's chainable builder methods."""

    keystates: List[Tuple[State, Optional[float], Optional[TransitionConfig]]] = field(
        default_factory=list
    )
    pending_transition: Optional[TransitionConfig] = None
    default_transition: Optional[TransitionConfig] = None
    attribute_path: Optional[Dict[str, PathFunction]] = None


class VElement(BaseVElement):
    """Central object that combines a renderer with its state(s)

    Can be used for static rendering (single state) or animation (keystates).
    Uses chainable methods for animation construction.

    Examples:
        # Static element
        element = VElement(state=static_state)

        # Animation with chainable methods
        element = (
            VElement()
            .renderer(CircleRenderer())
            .keystate(start_state, at=0.0)
            .transition(easing={"pos": easing.in_out})
            .keystate(end_state, at=1.0)
        )

        # Multiple keystates with automatic timing
        element = VElement().keystates([s1, s2, s3])
        element = VElement().keystates([s1, s2, s3], between=[0.2, 0.8])
        element = VElement().keystates([s1, s2, s3], at=[0.0, 0.3, 1.0])

    Elements only exist (render) within their keystate time range. If keystates
    don't cover the full [0, 1] timeline, the element won't render outside that range.
    """

    def __init__(
        self,
        renderer: Optional[Renderer] = None,
        state: Optional[State] = None,
    ) -> None:

        self._renderer = renderer

        # VElement-based clipping/masking
        self.clip_element = None
        self.mask_element = None
        self.clip_elements: List[VElement] = []

        # Vertex buffer cache for optimized interpolation
        self._vertex_buffer_cache: Dict[
            Tuple[int, int], Tuple[Points2D, List[Points2D]]
        ] = {}

        # Shape list matching cache for multi-shape morphing
        self._shape_list_cache: Dict[
            Tuple[str, int], Tuple[List[State], List[State]]
        ] = {}

        # Builder state for chainable methods
        self._builder: Optional[BuilderState] = BuilderState()

        # Store attribute config for later application (set via .attributes())
        self._attribute_easing: Optional[Dict[str, Callable[[float], float]]] = None
        self._attribute_keystates: Optional[AttributeKeyStatesConfig] = None

        # Defer BaseVElement initialization until _ensure_built()
        super().__init__(_defer_init=True)

        # Handle static state convenience parameter
        if state is not None:
            self.keystate(state)

    def _ensure_built(self) -> None:
        """Convert builder state to final keystates if not already done."""
        if self._builder is None:
            return

        # Validate minimum keystates for animation
        if len(self._builder.keystates) < 1:
            raise ValueError(
                "VElement requires at least 1 keystate. "
                "Use .keystate() to add states."
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
            # Merge element-level path into transition_config if needed
            effective_transition = self._merge_element_path_into_transition(
                transition_config
            )
            keystates.append(
                KeyState(state=state, time=time, transition_config=effective_transition)
            )

        # Clear builder state
        self._builder = None

        # Initialize BaseVElement systems (deferred from __init__)
        from svan2d.transition.easing_resolver import EasingResolver
        from svan2d.transition.path_resolver import PathResolver
        from svan2d.transition.interpolation_engine import InterpolationEngine
        from svan2d.velement.keystate_parser import (
            parse_element_keystates,
            parse_attribute_keystates,
        )

        self.easing_resolver = EasingResolver(self._attribute_easing)
        self._easing_resolver = self.easing_resolver  # Alias used by some methods
        self.path_resolver = PathResolver()
        self.interpolation_engine = InterpolationEngine(
            self.easing_resolver, self.path_resolver
        )

        self.attribute_keystates_raw = self._attribute_keystates or {}
        self.attribute_keystates = {}
        self.keystates = parse_element_keystates(keystates)

        # Parse attribute keystates if provided
        if self.attribute_keystates_raw:
            for field_name, timeline in self.attribute_keystates_raw.items():
                if not timeline:
                    raise ValueError(f"Empty timeline for field '{field_name}'")
                self.attribute_keystates[field_name] = parse_attribute_keystates(
                    timeline
                )

    def _merge_element_path_into_transition(
        self, transition_config: Optional[TransitionConfig]
    ) -> Optional[TransitionConfig]:
        """Merge element-level path config into segment transition."""
        if self._builder is None or self._builder.attribute_path is None:
            return transition_config

        if transition_config is None:
            return TransitionConfig(path=self._builder.attribute_path)

        # Segment path takes precedence, element path fills gaps
        segment_path = transition_config.path or {}
        merged_path = {**self._builder.attribute_path, **segment_path}

        return TransitionConfig(
            easing=transition_config.easing,
            morphing=transition_config.morphing,
            path=merged_path if merged_path else None,
        )

    def renderer(self, renderer: Renderer) -> "VElement":
        """Set the renderer for this element.

        Args:
            renderer: Renderer instance to use

        Returns:
            self for chaining
        """
        self._renderer = renderer
        return self

    def attributes(
        self,
        easing: Optional[Dict[str, Callable[[float], float]]] = None,
        path: Optional[Dict[str, PathFunction]] = None,
        keystates: Optional[AttributeKeyStatesConfig] = None,
    ) -> "VElement":
        """Set element-level attribute configuration.

        These settings apply to all segments unless overridden by
        segment-level transition() calls.

        Args:
            easing: Per-field easing functions {field_name: easing_func}
            path: Per-field path functions {field_name: path_func}
            keystates: Per-field keystate timelines {field_name: [values]}

        Returns:
            self for chaining
        """
        if easing is not None:
            self._attribute_easing = easing
        if path is not None:
            if self._builder is None:
                raise RuntimeError("Cannot modify VElement after rendering has begun.")
            self._builder.attribute_path = path
        if keystates is not None:
            self._attribute_keystates = keystates
        return self

    def clip(self, velement: "VElement") -> "VElement":
        """Add a clip element.

        Can be called multiple times to add multiple clips.

        Args:
            velement: VElement to use as clip mask

        Returns:
            self for chaining
        """
        self.clip_elements.append(velement)
        return self

    def mask(self, velement: "VElement") -> "VElement":
        """Set the mask element.

        Args:
            velement: VElement to use as mask

        Returns:
            self for chaining
        """
        self.mask_element = velement
        return self

    def default_transition(
        self,
        easing: Optional[Dict[str, Callable[[float], float]]] = None,
        path: Optional[Dict[str, PathFunction]] = None,
        morphing: Optional["Morphing"] = None,
    ) -> "VElement":
        """Set default transition parameters for all subsequent segments.

        These defaults apply to all following segments unless overridden
        by an explicit transition() call. Can be called multiple times
        to change defaults at different points in the builder chain.

        Args:
            easing: Per-field easing functions to use as default
            path: Per-field path functions to use as default
            morphing: Morphing configuration to use as default

        Returns:
            self for chaining

        Example:
            element = (
                VElement()
                .default_transition(easing={"pos": easing.in_out})
                .keystate(s1, at=0.0)
                .keystate(s2, at=0.3)  # uses in_out for pos
                .keystate(s3, at=0.5)  # uses in_out for pos
                .default_transition(easing={"pos": easing.linear})
                .keystate(s4, at=0.7)  # uses linear for pos
                .keystate(s5, at=1.0)  # uses linear for pos
            )
        """
        if self._builder is None:
            raise RuntimeError("Cannot modify VElement after rendering has begun.")

        # Create or update default transition config
        if self._builder.default_transition is None:
            self._builder.default_transition = TransitionConfig(
                easing=easing, path=path, morphing=morphing
            )
        else:
            # Merge with existing defaults
            merged_easing = self._builder.default_transition.easing or {}
            if easing:
                merged_easing = {**merged_easing, **easing}

            merged_path = self._builder.default_transition.path or {}
            if path:
                merged_path = {**merged_path, **path}

            merged_morphing = (
                morphing
                if morphing is not None
                else self._builder.default_transition.morphing
            )

            self._builder.default_transition = TransitionConfig(
                easing=merged_easing if merged_easing else None,
                path=merged_path if merged_path else None,
                morphing=merged_morphing,
            )
        return self

    def keystates(
        self,
        states: List[State],
        between: Optional[List[float]] = None,
        extend: bool = False,
        at: Optional[List[float]] = None,
    ) -> "VElement":
        """Add multiple keystates with automatic timing.

        Args:
            states: List of states to add
            between: Time range [start, end] for the states (default [0.0, 1.0])
            extend: If True and time range doesn't cover [0,1], extend with
                    copies of first/last state at 0.0/1.0
            at: Exact times for each state (overrides between if both given)

        Returns:
            self for chaining

        Example:
            # States at 0.0, 0.5, 1.0
            element.keystates([s1, s2, s3])

            # States at 0.2, 0.5, 0.8
            element.keystates([s1, s2, s3], between=[0.2, 0.8])

            # s1 at 0.0, s1 at 0.2, s2 at 0.5, s3 at 0.8, s3 at 1.0
            element.keystates([s1, s2, s3], between=[0.2, 0.8], extend=True)

            # Exact times
            element.keystates([s1, s2, s3], at=[0.2, 0.3, 0.8])
        """
        if not states:
            return self

        # Determine times for each state
        if at is not None:
            # Explicit times - validate length matches
            if len(at) != len(states):
                raise ValueError(
                    f"Length of 'at' ({len(at)}) must match length of 'states' ({len(states)})"
                )
            times = at
            start, end = times[0], times[-1]
        else:
            # Calculate from between range
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

    def keystate(self, state: State, at: Optional[float] = None) -> "VElement":
        """Add a keystate at the specified time.

        Args:
            state: State for this keystate
            at: Time position (0.0-1.0), or None for auto-timing

        Returns:
            self for chaining
        """
        if self._builder is None:
            raise RuntimeError("Cannot modify VElement after rendering has begun.")

        # Attach transition to previous keystate (explicit or default)
        if len(self._builder.keystates) > 0:
            prev_state, prev_time, _ = self._builder.keystates[-1]

            # Use pending explicit transition, or fall back to default
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

        # Add new keystate (transition will be attached when next keystate is added)
        self._builder.keystates.append((state, at, None))
        return self

    def transition(
        self,
        easing: Optional[Dict[str, Callable[[float], float]]] = None,
        path: Optional[Dict[str, PathFunction]] = None,
        morphing: Optional["Morphing"] = None,
    ) -> "VElement":
        """Configure the transition between the previous and next keystate.

        Multiple consecutive transition() calls merge their configurations.

        Args:
            easing: Per-field easing functions for this segment
            path: Per-field path functions for this segment
            morphing: Morphing configuration for vertex state transitions

        Returns:
            self for chaining

        Raises:
            RuntimeError: If called after rendering has begun
            ValueError: If called before any keystate
        """
        if self._builder is None:
            raise RuntimeError("Cannot modify VElement after rendering has begun.")

        if len(self._builder.keystates) == 0:
            raise ValueError("transition() cannot be called before the first keystate")

        # Merge with pending transition if exists
        if self._builder.pending_transition is None:
            self._builder.pending_transition = TransitionConfig(
                easing=easing, path=path, morphing=morphing
            )
        else:
            # Merge easing dicts
            merged_easing = self._builder.pending_transition.easing or {}
            if easing:
                merged_easing = {**merged_easing, **easing}

            # Merge path dicts
            merged_path = self._builder.pending_transition.path or {}
            if path:
                merged_path = {**merged_path, **path}

            # Morphing: later call overwrites (no merge - it's a single config)
            merged_morphing = (
                morphing
                if morphing is not None
                else self._builder.pending_transition.morphing
            )

            self._builder.pending_transition = TransitionConfig(
                easing=merged_easing if merged_easing else None,
                path=merged_path if merged_path else None,
                morphing=merged_morphing,
            )
        return self

    def get_frame(self, t: float) -> Optional[State]:
        """Get the interpolated state at a specific time

        Args:
            t: Time factor from 0.0 to 1.0

        Returns:
            Interpolated state at time t, or None if element doesn't exist at this time
        """
        self._ensure_built()
        state, _ = self._get_state_at_time(t)
        return state

    def render(self) -> Optional[dw.DrawingElement]:
        """Render the element in its current state (static rendering)

        Returns:
            drawsvg element representing the element, or None if element
            doesn't exist at t=0.0
        """
        return self.render_at_frame_time(0.0)

    def render_at_frame_time(
        self, t: float, drawing: Optional[dw.Drawing] = None
    ) -> Optional[dw.DrawingElement]:
        """Render the element at a specific animation frame_time

        Args:
            t: frame_time factor from 0.0 to 1.0
            drawing: Optional Drawing object for accessing defs section

        Returns:
            drawsvg element representing the element at time t, or None if
            element doesn't exist at this time (outside keystate range)
        """
        self._ensure_built()

        # Get the interpolated state at frame_time t
        interpolated_state, inbetween = self._get_state_at_time(t)

        # If no state (outside keystate range), don't render
        if interpolated_state is None:
            return None

        # Apply VElement-based clips
        if self.clip_element or self.mask_element or self.clip_elements:
            interpolated_state = self._apply_velement_clips(interpolated_state, t)

        if inbetween:
            renderer = VertexRenderer()
        else:
            if self._renderer:
                renderer = self._renderer
            else:
                renderer = get_renderer_instance_for_state(interpolated_state)

        return renderer.render(interpolated_state, drawing=drawing)

    def _apply_velement_clips(self, state: State, t: float) -> State:
        """Inject VElement-based clips into state"""
        from dataclasses import replace

        # Get clip states at time t
        mask_state_at_t = self.mask_element.get_frame(t) if self.mask_element else None
        clip_state_at_t = self.clip_element.get_frame(t) if self.clip_element else None
        clip_states_at_t = None

        if self.clip_elements:
            clip_states_at_t = [
                elem.get_frame(t)
                for elem in self.clip_elements
                if elem.get_frame(t) is not None
            ]

        # Inject into state
        return replace(
            state,
            clip_state=clip_state_at_t or state.clip_state,
            mask_state=mask_state_at_t or state.mask_state,
            clip_states=clip_states_at_t or state.clip_states,
        )

    def _get_vertex_buffer(
        self, num_verts: int, num_vertex_loops: int
    ) -> Tuple[Points2D, List[Points2D]]:
        """Get or create reusable vertex buffer for interpolation"""
        key = (num_verts, num_vertex_loops)
        if key not in self._vertex_buffer_cache:
            outer_buffer = [Point2D(0.0, 0.0) for _ in range(num_verts)]
            hole_buffers = [
                [Point2D(0.0, 0.0) for _ in range(num_verts)]
                for _ in range(num_vertex_loops)
            ]
            self._vertex_buffer_cache[key] = (outer_buffer, hole_buffers)

        return self._vertex_buffer_cache[key]

    def _ensure_shapes_matched(
        self,
        field_name: str,
        segment_idx: int,
        states1: List[State],
        states2: List[State],
    ) -> Tuple[List[State], List[State]]:
        """Cache M→N shape matching for list attributes"""
        cache_key = (field_name, segment_idx)

        if cache_key in self._shape_list_cache:
            return self._shape_list_cache[cache_key]

        from svan2d.transition.align_vertices import _get_vertex_loop_mapper_from_config

        mapper = _get_vertex_loop_mapper_from_config()

        from svan2d.transition.interpolation_engine import InterpolationEngine

        engine = InterpolationEngine(easing_resolver=self._easing_resolver)

        loops1 = [engine._state_to_vertex_loop(s) for s in states1]
        loops2 = [engine._state_to_vertex_loop(s) for s in states2]

        matched_loops1, matched_loops2 = mapper.map(loops1, loops2)

        matched_states1 = engine._loops_to_states(matched_loops1, states1)
        matched_states2 = engine._loops_to_states(matched_loops2, states2)

        result = (matched_states1, matched_states2)
        self._shape_list_cache[cache_key] = result
        return result

    def is_animatable(self) -> bool:
        """Check if this element can be animated"""
        self._ensure_built()
        return super().is_animatable()
