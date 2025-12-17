"""VElement class - the central object that combines renderers and states."""

from __future__ import annotations
from dataclasses import replace
from typing import Optional, Dict, Callable, List, Tuple, TYPE_CHECKING

import drawsvg as dw

from svan2d.component import Renderer, State, get_renderer_instance_for_state
from svan2d.velement.base_velement import BaseVElement
from svan2d.velement.builder import KeystateBuilder, BuilderState
from svan2d.velement.state_interpolator import StateInterpolator
from svan2d.velement.vertex_alignment import VertexAligner
from svan2d.component.renderer.base_vertex import VertexRenderer
from svan2d.velement.keystate_parser import AttributeKeyStatesDict
from svan2d.core.point2d import Point2D, Points2D
from svan2d.velement.keystate import KeyState

if TYPE_CHECKING:
    from svan2d.velement.morphing import Morphing


class VElement(BaseVElement, KeystateBuilder):
    """Central object that combines a renderer with its state(s).

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
            .transition(easing_dict={"pos": easing.in_out})
            .keystate(end_state, at=1.0)
        )

        # Multiple keystates with automatic timing
        element = VElement().keystates([s1, s2, s3])
    """

    def __init__(
        self,
        renderer: Optional[Renderer] = None,
        state: Optional[State] = None,
    ) -> None:
        self._renderer = renderer

        # Clip/mask elements
        self.clip_element: Optional[VElement] = None
        self.mask_element: Optional[VElement] = None
        self.clip_elements: List[VElement] = []

        # Vertex buffer cache for optimized interpolation
        self._vertex_buffer_cache: Dict[
            Tuple[int, int], Tuple[Points2D, List[Points2D]]
        ] = {}

        # Shape list matching cache for multi-shape morphing
        self._shape_list_cache: Dict[
            Tuple[str, int], Tuple[List[State], List[State]]
        ] = {}

        # Builder state (from KeystateBuilder mixin)
        self._builder: Optional[BuilderState] = BuilderState()
        self._attribute_easing: Optional[Dict[str, Callable[[float], float]]] = None
        self._attribute_keystates: Optional[AttributeKeyStatesDict] = None

        # Interpolator (created on first render)
        self._interpolator: Optional[StateInterpolator] = None

        # Handle static state convenience parameter
        if state is not None:
            self.keystate(state)

    def _ensure_built(self) -> None:
        """Convert builder state to final keystates if not already done."""
        if self._builder is None:
            return

        # Use builder mixin to finalize
        keystates, attribute_keystates = self._finalize_build()

        # Initialize interpolation systems
        from svan2d.transition.easing_resolver import EasingResolver
        from svan2d.transition.path_resolver import PathResolver
        from svan2d.transition.interpolation_engine import InterpolationEngine

        easing_resolver = EasingResolver(self._attribute_easing)
        self.easing_resolver = easing_resolver  # Keep for shape matching
        path_resolver = PathResolver()
        interpolation_engine = InterpolationEngine(easing_resolver, path_resolver)

        # Store keystates and create interpolator
        self.keystates = keystates
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
        """Set the renderer for this element."""
        self._renderer = renderer
        return self

    def clip(self, velement: "VElement") -> "VElement":
        """Add a clip element. Can be called multiple times."""
        self.clip_elements.append(velement)
        return self

    def mask(self, velement: "VElement") -> "VElement":
        """Set the mask element."""
        self.mask_element = velement
        return self

    def segment(self, segment_result: List[KeyState]) -> "VElement":
        """Add keystates from a segment function result."""
        if self._builder is None:
            raise RuntimeError("Cannot modify VElement after rendering has begun.")

        for ks in segment_result:
            self._builder.keystates.append((ks.state, ks.time, ks.transition_config, ks.skip_render_at))

        return self

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
        state, _ = self._interpolator.get_state_at_time(t)
        return state

    def is_animatable(self) -> bool:
        """Check if this element can be animated."""
        self._ensure_built()
        return len(self.keystates) > 1 or bool(self.attribute_keystates)

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

        from svan2d.transition.align_vertices import _get_vertex_loop_mapper_from_config
        from svan2d.transition.interpolation_engine import InterpolationEngine

        mapper = _get_vertex_loop_mapper_from_config()
        engine = InterpolationEngine(easing_resolver=self.easing_resolver)

        loops1 = [engine._state_to_vertex_loop(s) for s in states1]
        loops2 = [engine._state_to_vertex_loop(s) for s in states2]

        matched_loops1, matched_loops2 = mapper.map(loops1, loops2)

        matched_states1 = engine._loops_to_states(matched_loops1, states1)
        matched_states2 = engine._loops_to_states(matched_loops2, states2)

        result = (matched_states1, matched_states2)
        self._shape_list_cache[cache_key] = result
        return result
