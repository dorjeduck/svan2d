"""VElementGroup class - element transform groups with animation support."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, cast

import drawsvg as dw

from svan2d.component.state.base import State
from svan2d.velement.base_velement import BaseVElement
from svan2d.velement.builder import BuilderState, KeystateBuilder
from svan2d.velement.keystate_parser import AttributeKeyStatesDict
from svan2d.velement.transition import EasingFunction
from svan2d.velement.state_interpolator import StateInterpolator

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


class VElementGroup(BaseVElement, KeystateBuilder):
    """Element transform group with complete SVG transform capabilities.

    Uses chainable builder pattern for animation construction. All methods
    return new instances (immutable pattern).

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

    def __init__(
        self,
        elements: Optional[List[VElement]] = None,
        group_easing: Optional[Callable[[float], float]] = None,
        *,
        # Private params for _replace - don't use directly
        _builder: Optional[BuilderState] = None,
        _clip_elements: Optional[List[VElement]] = None,
        _mask_element: Optional[VElement] = None,
        _attribute_easing: Optional[Dict[str, EasingFunction]] = None,
        _attribute_keystates: Optional[AttributeKeyStatesDict] = None,
    ) -> None:
        """Initialize an element group with builder pattern.

        Args:
            elements: Optional initial list of child elements
            group_easing: Optional easing function applied to the group's animation time
        """
        self.elements: List[VElement] = list(elements) if elements else []
        self.group_easing = group_easing

        # Clip/mask elements
        self.clip_elements: List[VElement] = _clip_elements if _clip_elements is not None else []
        self.mask_element: Optional[VElement] = _mask_element

        # Builder state (from KeystateBuilder mixin)
        self._builder: Optional[BuilderState] = _builder if _builder is not None else BuilderState()
        self._attribute_easing: Optional[Dict[str, EasingFunction]] = _attribute_easing
        self._attribute_keystates: Optional[AttributeKeyStatesDict] = _attribute_keystates

        # Interpolator (created on first render)
        self._interpolator: Optional[StateInterpolator] = None

        # Cache last frame time for render_state (set by get_frame)
        self._last_frame_time: float = 0.0

    def _replace(
        self,
        *,
        elements: Optional[List[VElement]] = None,
        group_easing: Optional[Callable[[float], float]] = ...,  # type: ignore[assignment]
        clip_elements: Optional[List[VElement]] = None,
        mask_element: Optional[VElement] = ...,  # type: ignore[assignment]
        builder: Optional[BuilderState] = None,
        attribute_easing: Optional[Dict[str, EasingFunction]] = None,
        attribute_keystates: Optional[AttributeKeyStatesDict] = None,
    ) -> "VElementGroup":
        """Return a new VElementGroup with specified attributes replaced."""
        new = VElementGroup.__new__(VElementGroup)
        new.elements = elements if elements is not None else self.elements.copy()
        new.group_easing = self.group_easing if group_easing is ... else group_easing
        new.clip_elements = clip_elements if clip_elements is not None else self.clip_elements.copy()
        new.mask_element = self.mask_element if mask_element is ... else mask_element
        new._builder = builder if builder is not None else self._builder
        new._attribute_easing = attribute_easing if attribute_easing is not None else self._attribute_easing
        new._attribute_keystates = attribute_keystates if attribute_keystates is not None else self._attribute_keystates
        new._interpolator = None
        new._last_frame_time = 0.0
        return new

    def _replace_builder(self, new_builder: BuilderState) -> "VElementGroup":
        """Return a new VElementGroup with the updated builder state."""
        return self._replace(builder=new_builder)

    def _replace_attributes(
        self,
        new_builder: BuilderState,
        new_easing: Optional[Dict[str, EasingFunction]],
        new_keystates: Optional[AttributeKeyStatesDict],
    ) -> "VElementGroup":
        """Return a new VElementGroup with updated builder and attribute settings."""
        return self._replace(
            builder=new_builder,
            attribute_easing=new_easing,
            attribute_keystates=new_keystates,
        )

    def _ensure_built(self) -> None:
        """Convert builder state to final keystates if not already done."""
        if self._builder is None:
            return

        # Auto-create identity keystates if group_easing is set but no keystates defined
        if self.group_easing is not None and len(self._builder.keystates) == 0:
            identity = VElementGroupState()
            # Tuple format: (state, outgoing_state, time, transition_config, render_index)
            self._builder.keystates.append((identity, None, 0.0, None, None))
            self._builder.keystates.append((identity, None, 1.0, None, None))

        # Use builder mixin to finalize
        keystates, attribute_keystates = self._finalize_build()

        # Initialize interpolation systems
        from svan2d.transition.easing_resolver import EasingResolver
        from svan2d.transition.interpolation_engine import InterpolationEngine

        easing_resolver = EasingResolver(self._attribute_easing)
        interpolation_engine = InterpolationEngine(easing_resolver)

        # Store keystates and create interpolator (no vertex aligner for groups)
        self._keystates_list = keystates
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
        """Add a clip element. Can be called multiple times. Returns new VElementGroup."""
        return self._replace(clip_elements=self.clip_elements + [velement])

    def mask(self, velement: "VElement") -> "VElementGroup":
        """Set the mask element. Returns new VElementGroup."""
        return self._replace(mask_element=velement)

    # =========================================================================
    # Element Management Methods (chainable, immutable)
    # =========================================================================

    def add_element(self, child: "VElement") -> "VElementGroup":
        """Add a child element to the group. Returns new VElementGroup."""
        return self._replace(elements=self.elements + [child])

    def add_elements(self, elements: List["VElement"]) -> "VElementGroup":
        """Add multiple child elements to the group. Returns new VElementGroup."""
        return self._replace(elements=self.elements + list(elements))

    def remove_element(self, child: "VElement") -> "VElementGroup":
        """Remove a child element from the group. Returns new VElementGroup."""
        if child not in self.elements:
            raise ValueError("Element not found in group")
        return self._replace(elements=[e for e in self.elements if e is not child])

    def clear_elements(self) -> "VElementGroup":
        """Remove all child elements from the group. Returns new VElementGroup."""
        return self._replace(elements=[])

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
        assert self._interpolator is not None

        if self.group_easing is not None:
            t = self.group_easing(t)

        group_state, _ = self._interpolator.get_state_at_time(t)

        if group_state is None:
            return None

        group_state = cast(VElementGroupState, group_state)

        # Apply clip/mask if present
        if self.clip_elements or self.mask_element:
            group_state = self._apply_velement_clips(group_state, t)

        transform_string = self._build_transform_string(group_state)

        if transform_string:
            group = dw.Group(transform=transform_string)
        else:
            group = dw.Group()

        # Sort children by z_index (stable sort preserves insertion order for equal z_index)
        def get_z_index(element: "VElement") -> float:
            if hasattr(element, "get_frame"):
                state = element.get_frame(t)
                if state is not None:
                    return state.z_index
            return 0.0

        sorted_children = sorted(self.elements, key=get_z_index)

        for child in sorted_children:
            child_element = None
            if hasattr(child, "render_at_frame_time") and child.is_animatable():
                child_element = child.render_at_frame_time(t)
            else:
                child_element = child.render()

            if child_element is not None:
                group.append(child_element)

        if group_state.opacity != 1.0:
            group.opacity = group_state.opacity  # type: ignore[attr-defined]

        return group

    def get_frame(self, t: float) -> Optional[VElementGroupState]:
        """Get the interpolated state at a specific time."""
        self._ensure_built()
        assert self._interpolator is not None

        if self.group_easing is not None:
            t = self.group_easing(t)

        self._last_frame_time = t  # Cache for render_state
        state, _ = self._interpolator.get_state_at_time(t)
        return cast(VElementGroupState, state) if state is not None else None

    def render_state(
        self, state: VElementGroupState, drawing: Optional[dw.Drawing] = None
    ) -> Optional[dw.Group]:
        """Render a pre-computed state directly (avoids re-interpolation).

        Uses _last_frame_time (set by get_frame) to render children at the correct time.
        """
        if state is None:
            return None

        t = self._last_frame_time

        # Apply clip/mask if present
        if self.clip_elements or self.mask_element:
            state = self._apply_velement_clips(state, t)

        transform_string = self._build_transform_string(state)

        if transform_string:
            group = dw.Group(transform=transform_string)
        else:
            group = dw.Group()

        # Sort children by z_index
        def get_z_index(element: "VElement") -> float:
            if hasattr(element, "get_frame"):
                child_state = element.get_frame(t)
                if child_state is not None:
                    return child_state.z_index
            return 0.0

        sorted_children = sorted(self.elements, key=get_z_index)

        for child in sorted_children:
            child_element = None
            if hasattr(child, "render_at_frame_time") and child.is_animatable():
                child_element = child.render_at_frame_time(t)
            else:
                child_element = child.render()

            if child_element is not None:
                group.append(child_element)

        if state.opacity != 1.0:
            group.opacity = state.opacity  # type: ignore[attr-defined]

        return group

    def is_animatable(self) -> bool:
        """Check if this group can be animated."""
        self._ensure_built()
        return len(self._keystates_list) > 1 or bool(self.attribute_keystates)

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
            assert state.scale is not None
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
