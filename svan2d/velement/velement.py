"""VElement class - the central object that combines renderers and states."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple

import drawsvg as dw

from svan2d.component import (
    Renderer,
    State,
    VertexState,
    get_renderer_instance_for_state,
)
from svan2d.component.renderer.base_vertex import VertexRenderer
from svan2d.core.point2d import Point2D, Points2D
from svan2d.velement.base_velement import BaseVElement
from svan2d.velement.builder import BuilderState, KeystateBuilder
from svan2d.velement.keystate import KeyState
from svan2d.velement.keystate_parser import AttributeKeyStatesDict
from svan2d.velement.transition import EasingFunction
from svan2d.velement.state_interpolator import StateInterpolator
from svan2d.velement.vertex_alignment import VertexAligner

if TYPE_CHECKING:
    from svan2d.velement.morphing import MorphingConfig


class VElement(BaseVElement, KeystateBuilder):
    """Central object that combines a renderer with its state(s).

    Can be used for static rendering (single state) or animation (keystates).
    Uses chainable methods for animation construction. All methods return new
    instances (immutable pattern).

    Examples:
        # Static element
        element = VElement(state=static_state)

        # Animation with chainable methods
        element = (
            VElement()
            .renderer(CircleRenderer())
            .keystate(start_state, at=0.0)
            .transition(easing_dict={"pos": easing.in_out})
            .keystate(end_state, at=1.0)
        )

        # Multiple keystates with automatic timing
        element = VElement().keystates([s1, s2, s3])
    """

    __slots__ = (
        "_renderer",
        "clip_element",
        "mask_element",
        "clip_elements",
        "_vertex_buffer_cache",
        "_shape_list_cache",
        "_builder",
        "_attribute_easing",
        "_attribute_keystates",
        "_interpolator",
        "_keystates_list",
        "attribute_keystates",
        "easing_resolver",
    )

    def __init__(
        self,
        renderer: Optional[Renderer] = None,
        state: State | None = None,
        *,
        # Private params for _replace - don't use directly
        _builder: Optional[BuilderState] = None,
        _clip_elements: Optional[List["VElement"]] = None,
        _mask_element: Optional["VElement"] = None,
        _attribute_easing: Optional[Dict[str, EasingFunction]] = None,
        _attribute_keystates: Optional[AttributeKeyStatesDict] = None,
    ) -> None:
        self._renderer = renderer

        # Clip/mask elements
        self.clip_element: Optional[VElement] = None
        self.mask_element: Optional[VElement] = _mask_element
        self.clip_elements: List[VElement] = _clip_elements if _clip_elements is not None else []

        # Vertex buffer cache for optimized interpolation
        self._vertex_buffer_cache: Dict[
            Tuple[int, int], Tuple[Points2D, List[Points2D]]
        ] = {}

        # Shape list matching cache for multi-shape morphing
        self._shape_list_cache: Dict[
            Tuple[str, int], Tuple[List[State], List[State]]
        ] = {}

        # Builder state (from KeystateBuilder mixin)
        self._builder: Optional[BuilderState] = _builder if _builder is not None else BuilderState()
        self._attribute_easing: Optional[Dict[str, EasingFunction]] = _attribute_easing
        self._attribute_keystates: Optional[AttributeKeyStatesDict] = _attribute_keystates

        # Interpolator (created on first render)
        self._interpolator: Optional[StateInterpolator] = None

        # Handle static state convenience parameter
        if state is not None:
            # Chain immutably - replace self with new instance
            new_self = self.keystate(state)
            # Copy all attributes from new_self to self
            self._builder = new_self._builder
            self._attribute_easing = new_self._attribute_easing
            self._attribute_keystates = new_self._attribute_keystates
            self.clip_elements = new_self.clip_elements
            self.mask_element = new_self.mask_element

    def _replace(
        self,
        *,
        renderer: Optional[Renderer] = None,
        clip_elements: Optional[List["VElement"]] = None,
        mask_element: Optional["VElement"] = ...,  # type: ignore[assignment]
        builder: Optional[BuilderState] = None,
        attribute_easing: Optional[Dict[str, EasingFunction]] = None,
        attribute_keystates: Optional[AttributeKeyStatesDict] = None,
    ) -> "VElement":
        """Return a new VElement with specified attributes replaced."""
        # Use sentinel value for mask_element to distinguish None from "not provided"
        new = VElement.__new__(VElement)
        new._renderer = renderer if renderer is not None else self._renderer
        new.clip_element = None
        new.mask_element = self.mask_element if mask_element is ... else mask_element
        new.clip_elements = clip_elements if clip_elements is not None else self.clip_elements.copy()
        new._vertex_buffer_cache = {}
        new._shape_list_cache = {}
        new._builder = builder if builder is not None else self._builder
        new._attribute_easing = attribute_easing if attribute_easing is not None else self._attribute_easing
        new._attribute_keystates = attribute_keystates if attribute_keystates is not None else self._attribute_keystates
        new._interpolator = None
        return new

    def _replace_builder(self, new_builder: BuilderState) -> "VElement":
        """Return a new VElement with the updated builder state."""
        return self._replace(builder=new_builder)

    def _replace_attributes(
        self,
        new_builder: BuilderState,
        new_easing: Optional[Dict[str, EasingFunction]],
        new_keystates: Optional[AttributeKeyStatesDict],
    ) -> "VElement":
        """Return a new VElement with updated builder and attribute settings."""
        return self._replace(
            builder=new_builder,
            attribute_easing=new_easing,
            attribute_keystates=new_keystates,
        )

    def _ensure_built(self) -> None:
        """Convert builder state to final keystates if not already done."""
        if self._builder is None:
            return

        # Use builder mixin to finalize
        keystates, attribute_keystates = self._finalize_build()

        # Initialize interpolation systems
        from svan2d.transition.easing_resolver import EasingResolver
        from svan2d.transition.interpolation_engine import InterpolationEngine
        from svan2d.transition.path_resolver import PathResolver

        easing_resolver = EasingResolver(self._attribute_easing)
        self.easing_resolver = easing_resolver  # Keep for shape matching
        path_resolver = PathResolver()
        interpolation_engine = InterpolationEngine(easing_resolver, path_resolver)

        # Store keystates and create interpolator
        self._keystates_list = keystates
        self.attribute_keystates = attribute_keystates

        self._interpolator = StateInterpolator(
            keystates=keystates,
            attribute_keystates=attribute_keystates,
            easing_resolver=easing_resolver,
            interpolation_engine=interpolation_engine,
            vertex_aligner=VertexAligner(),
            get_vertex_buffer=self._get_vertex_buffer,
        )

    # =========================================================================
    # VElement-specific builder methods
    # =========================================================================

    def renderer(self, renderer: Renderer) -> "VElement":
        """Set the renderer for this element. Returns new VElement."""
        return self._replace(renderer=renderer)

    def clip(self, velement: "VElement") -> "VElement":
        """Add a clip element. Can be called multiple times. Returns new VElement."""
        return self._replace(clip_elements=self.clip_elements + [velement])

    def mask(self, velement: "VElement") -> "VElement":
        """Set the mask element. Returns new VElement."""
        return self._replace(mask_element=velement)

    def segment(self, segment_result: List[KeyState]) -> "VElement":
        """Add keystates from a segment function result. Returns new VElement."""
        if self._builder is None:
            raise RuntimeError("Cannot modify VElement after rendering has begun.")

        # Build new keystates tuple
        new_keystates = self._builder.keystates + tuple(
            (ks.state, ks.outgoing_state, ks.time, ks.transition_config, ks.render_index)
            for ks in segment_result
        )
        new_builder = BuilderState(
            keystates=new_keystates,
            pending_transition=self._builder.pending_transition,
            default_transition=self._builder.default_transition,
            curve_dict=self._builder.curve_dict,
        )
        return self._replace(builder=new_builder)

    # =========================================================================
    # Rendering
    # =========================================================================

    def render(self) -> Optional[dw.DrawingElement]:
        """Render the element in its initial state."""
        return self.render_at_frame_time(0.0)

    def render_at_frame_time(
        self, t: float, drawing: Optional[dw.Drawing] = None
    ) -> Optional[dw.DrawingElement]:
        """Render the element at a specific animation time."""
        self._ensure_built()
        assert self._interpolator is not None

        interpolated_state, inbetween = self._interpolator.get_state_at_time(t)

        if interpolated_state is None:
            return None

        # Apply clips/masks
        if self.clip_element or self.mask_element or self.clip_elements:
            interpolated_state = self._apply_velement_clips(interpolated_state, t)

        # Select renderer
        if inbetween:
            renderer = VertexRenderer()
        elif self._renderer:
            renderer = self._renderer
        else:
            renderer = get_renderer_instance_for_state(interpolated_state)

        return renderer.render(interpolated_state, drawing=drawing)

    def get_frame(self, t: float) -> Optional[State]:
        """Get the interpolated state at a specific time."""
        self._ensure_built()
        assert self._interpolator is not None
        state, _ = self._interpolator.get_state_at_time(t)
        return state

    def render_state(
        self, state: State, drawing: Optional[dw.Drawing] = None
    ) -> Optional[dw.DrawingElement]:
        """Render a pre-computed state directly (avoids re-interpolation)."""
        if state is None:
            return None

        # Check if this is a morph transition (VertexState with aligned contours)
        if isinstance(state, VertexState) and state._aligned_contours is not None:
            renderer = VertexRenderer()
        elif self._renderer:
            renderer = self._renderer
        else:
            renderer = get_renderer_instance_for_state(state)

        return renderer.render(state, drawing=drawing)

    def is_animatable(self) -> bool:
        """Check if this element can be animated."""
        self._ensure_built()
        return len(self._keystates_list) > 1 or bool(self.attribute_keystates)

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _apply_velement_clips(self, state: State, t: float) -> State:
        """Inject VElement-based clips into state."""
        mask_state_at_t = self.mask_element.get_frame(t) if self.mask_element else None
        clip_state_at_t = self.clip_element.get_frame(t) if self.clip_element else None
        clip_states_at_t = None

        if self.clip_elements:
            clip_states_at_t = [
                elem.get_frame(t)
                for elem in self.clip_elements
                if elem.get_frame(t) is not None
            ]

        return replace(
            state,
            clip_state=clip_state_at_t or state.clip_state,
            mask_state=mask_state_at_t or state.mask_state,
            clip_states=clip_states_at_t or state.clip_states,
        )

    def _get_vertex_buffer(
        self, num_verts: int, num_vertex_loops: int
    ) -> Tuple[Points2D, List[Points2D]]:
        """Get or create reusable vertex buffer for interpolation."""
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
        """Cache M→N shape matching for list attributes."""
        cache_key = (field_name, segment_idx)

        if cache_key in self._shape_list_cache:
            return self._shape_list_cache[cache_key]

        from svan2d.transition.align_vertices import _get_mapper_from_config

        mapper = _get_mapper_from_config()
        matches = mapper.map(states1, states2, lambda s: s.pos or Point2D(0, 0))

        # Build matched state lists from matches
        matched_states1 = []
        matched_states2 = []
        for match in matches:
            if match.is_morph:
                matched_states1.append(match.start)
                matched_states2.append(match.end)
            elif match.is_destruction:
                matched_states1.append(match.start)
                matched_states2.append(match.start)  # Morph to self (will fade out)
            elif match.is_creation:
                matched_states1.append(match.end)  # Morph from self (will fade in)
                matched_states2.append(match.end)

        result = (matched_states1, matched_states2)
        self._shape_list_cache[cache_key] = result
        return result
