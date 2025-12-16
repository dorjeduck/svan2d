"""VElementGroup class - element transform groups with animation support."""

from __future__ import annotations
from dataclasses import dataclass, replace
from typing import List, Optional, Dict, Callable, TYPE_CHECKING

import drawsvg as dw

from svan2d.component import State
from svan2d.velement.base_velement import BaseVElement
from svan2d.velement.builder import KeystateBuilder, BuilderState
from svan2d.velement.state_interpolator import StateInterpolator
from svan2d.velement.keystate_parser import AttributeKeyStatesDict
from svan2d.transition import easing

if TYPE_CHECKING:
    from .velement import VElement


@dataclass(frozen=True)
class VElementGroupState(State):
    """State class for element transform groups with complete SVG transform capabilities."""

    transform_origin_x: float = 0
    transform_origin_y: float = 0
    scale_x: float = 1.0
    scale_y: float = 1.0
    skew_x: float = 0
    skew_y: float = 0

    DEFAULT_EASING = {
        **State.DEFAULT_EASING,
        "transform_origin_x": easing.in_out,
        "transform_origin_y": easing.in_out,
        "scale_x": easing.in_out,
        "scale_y": easing.in_out,
        "skew_x": easing.in_out,
        "skew_y": easing.in_out,
    }


class VElementGroup(BaseVElement, KeystateBuilder):
    """Element transform group with complete SVG transform capabilities.

    Uses chainable builder pattern for animation construction.

    Examples:
        # Static group
        group = VElementGroup(elements=[e1, e2]).keystate(VElementGroupState())

        # Animated group
        group = (
            VElementGroup(elements=[e1, e2])
            .keystate(VElementGroupState(rotation=0), at=0.0)
            .transition(easing_dict={"rotation": easing.in_out})
            .keystate(VElementGroupState(rotation=90), at=1.0)
        )

        # Multiple keystates with automatic timing
        group = (
            VElementGroup()
            .add_elements([e1, e2])
            .keystates([s1, s2, s3])
        )
    """

    def __init__(self, elements: Optional[List[VElement]] = None) -> None:
        """Initialize an element group with builder pattern.

        Args:
            elements: Optional initial list of child elements
        """
        self.elements: List[VElement] = elements if elements else []

        # Clip/mask elements
        self.clip_elements: List[VElement] = []
        self.mask_element: Optional[VElement] = None

        # Builder state (from KeystateBuilder mixin)
        self._builder: Optional[BuilderState] = BuilderState()
        self._attribute_easing: Optional[Dict[str, Callable[[float], float]]] = None
        self._attribute_keystates: Optional[AttributeKeyStatesDict] = None

        # Interpolator (created on first render)
        self._interpolator: Optional[StateInterpolator] = None

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
        path_resolver = PathResolver()
        interpolation_engine = InterpolationEngine(easing_resolver, path_resolver)

        # Store keystates and create interpolator (no vertex aligner for groups)
        self.keystates = keystates
        self.attribute_keystates = attribute_keystates

        self._interpolator = StateInterpolator(
            keystates=keystates,
            attribute_keystates=attribute_keystates,
            easing_resolver=easing_resolver,
            interpolation_engine=interpolation_engine,
            # No vertex_aligner - groups don't morph shapes
            # No get_vertex_buffer - groups don't have vertices
        )

    # =========================================================================
    # VElementGroup-specific builder methods
    # =========================================================================

    def clip(self, velement: "VElement") -> "VElementGroup":
        """Add a clip element. Can be called multiple times."""
        self.clip_elements.append(velement)
        return self

    def mask(self, velement: "VElement") -> "VElementGroup":
        """Set the mask element."""
        self.mask_element = velement
        return self

    # =========================================================================
    # Element Management Methods (chainable)
    # =========================================================================

    def add_element(self, child: "VElement") -> "VElementGroup":
        """Add a child element to the group."""
        self.elements.append(child)
        return self

    def add_elements(self, elements: List["VElement"]) -> "VElementGroup":
        """Add multiple child elements to the group."""
        self.elements.extend(elements)
        return self

    def remove_element(self, child: "VElement") -> "VElementGroup":
        """Remove a child element from the group."""
        if child in self.elements:
            self.elements.remove(child)
        else:
            raise ValueError("Element not found in group")
        return self

    def clear_elements(self) -> "VElementGroup":
        """Remove all child elements from the group."""
        self.elements.clear()
        return self

    def get_elements(self) -> List["VElement"]:
        """Get the list of child elements."""
        return self.elements.copy()

    def is_empty(self) -> bool:
        """Check if the group has no child elements."""
        return len(self.elements) == 0

    # =========================================================================
    # Rendering
    # =========================================================================

    def render(self) -> Optional[dw.Group]:
        """Render the element group in its initial state."""
        return self.render_at_frame_time(0.0)

    def render_at_frame_time(
        self, t: float, drawing: Optional[dw.Drawing] = None
    ) -> Optional[dw.Group]:
        """Render the element transform group at a specific animation time."""
        self._ensure_built()

        group_state, _ = self._interpolator.get_state_at_time(t)

        if group_state is None:
            return None

        # Apply clip/mask if present
        if self.clip_elements or self.mask_element:
            group_state = self._apply_velement_clips(group_state, t)

        transform_string = self._build_transform_string(group_state)

        if transform_string:
            group = dw.Group(transform=transform_string)
        else:
            group = dw.Group()

        for child in self.elements:
            child_element = None
            if hasattr(child, "render_at_frame_time") and child.is_animatable():
                child_element = child.render_at_frame_time(t)
            else:
                child_element = child.render()

            if child_element is not None:
                group.append(child_element)

        if group_state.opacity != 1.0:
            group.opacity = group_state.opacity

        return group

    def get_frame(self, t: float) -> Optional[VElementGroupState]:
        """Get the interpolated state at a specific time."""
        self._ensure_built()
        state, _ = self._interpolator.get_state_at_time(t)
        return state

    def is_animatable(self) -> bool:
        """Check if this group can be animated."""
        self._ensure_built()
        return len(self.keystates) > 1 or bool(self.attribute_keystates)

    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _apply_velement_clips(
        self, state: VElementGroupState, t: float
    ) -> VElementGroupState:
        """Inject VElement-based clips into state."""
        mask_state_at_t = self.mask_element.get_frame(t) if self.mask_element else None
        clip_states_at_t = None

        if self.clip_elements:
            clip_states_at_t = [
                elem.get_frame(t)
                for elem in self.clip_elements
                if elem.get_frame(t) is not None
            ]

        return replace(
            state,
            mask_state=mask_state_at_t or state.mask_state,
            clip_states=clip_states_at_t or state.clip_states,
        )

    def _build_transform_string(self, state: VElementGroupState) -> str:
        """Build SVG transform string from state with advanced transform support."""
        transform_parts = []

        has_transform_origin = (
            state.transform_origin_x != 0 or state.transform_origin_y != 0
        )
        has_rotation = state.rotation != 0
        has_non_uniform_scale = (
            state.scale_x != 1.0 or state.scale_y != 1.0
        ) or state.scale != 1.0
        has_skew = state.skew_x != 0 or state.skew_y != 0

        if has_transform_origin and (has_rotation or has_non_uniform_scale or has_skew):
            transform_parts.append(
                f"translate({state.transform_origin_x}, {state.transform_origin_y})"
            )

        if state.x != 0 or state.y != 0:
            transform_parts.append(f"translate({state.x}, {state.y})")

        if state.rotation != 0:
            transform_parts.append(f"rotate({state.rotation})")

        if state.scale != 1.0 and (state.scale_x == 1.0 and state.scale_y == 1.0):
            transform_parts.append(f"scale({state.scale})")
        elif state.scale_x != 1.0 or state.scale_y != 1.0:
            final_scale_x = state.scale_x * state.scale
            final_scale_y = state.scale_y * state.scale
            transform_parts.append(f"scale({final_scale_x}, {final_scale_y})")
        elif state.scale != 1.0:
            transform_parts.append(f"scale({state.scale})")

        if state.skew_x != 0:
            transform_parts.append(f"skewX({state.skew_x})")

        if state.skew_y != 0:
            transform_parts.append(f"skewY({state.skew_y})")

        if has_transform_origin and (has_rotation or has_non_uniform_scale or has_skew):
            transform_parts.append(
                f"translate({-state.transform_origin_x}, {-state.transform_origin_y})"
            )

        return " ".join(transform_parts)
