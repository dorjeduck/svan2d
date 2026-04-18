"""Abstract base classes for renderers and states in the svan2d framework"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from svan2d.primitive.state.base import State
    from svan2d.primitive.state.base_vertex import VertexState

import drawsvg as dw


def _set_elem_attr(elem: dw.DrawingElement, key: str, value: Any) -> None:
    """Set an attribute on a drawsvg element.

    drawsvg elements store attributes in an 'args' dict.
    This helper encapsulates access to the untyped drawsvg internals.
    """
    args = getattr(elem, "args", None)
    if args is not None:
        args[key] = value


class Renderer(ABC):
    """Abstract base class for all renderer classes

    Each renderer must implement core geometry in _render_core.
    The base render method applies transforms and opacity.
    """

    @staticmethod
    def _build_transform_string(state: State) -> str | None:
        """Build SVG transform attribute string from state fields.

        Returns None if no transforms are needed.
        """

        transforms = []
        if state.pos != None and (state.pos.x != 0 or state.pos.y != 0):
            transforms.append(f"translate({state.pos.x},{-state.pos.y})")
        if state.rotation is not None and state.rotation != 0:
            transforms.append(f"rotate({-state.rotation})")
        if state.scale != 1.0 and state.scale != None:
            transforms.append(f"scale({state.scale})")
        if state.skew_x:
            transforms.append(f"skewX({-state.skew_x})")
        if state.skew_y:
            transforms.append(f"skewY({-state.skew_y})")
        return " ".join(transforms) if transforms else None

    @staticmethod
    def _render_state_element(
        state: State, drawing: dw.Drawing | None = None
    ) -> dw.DrawingElement:
        """Render a state's core element, handling morph detection.

        If state has _aligned_contours, uses VertexRenderer for morphing.
        Otherwise uses the registered renderer for the state type.
        """
        from svan2d.primitive import get_renderer_instance_for_state
        from svan2d.primitive.renderer.base_vertex import VertexRenderer

        aligned_contours = getattr(state, "_aligned_contours", None)
        if aligned_contours is not None:
            renderer: Renderer = VertexRenderer()
            return renderer._render_core(cast("VertexState", state), drawing=drawing)
        else:
            renderer = get_renderer_instance_for_state(state)
            return renderer._render_core(state, drawing=drawing)

    @abstractmethod
    def _render_core(
        self, state: State, drawing: dw.Drawing | None = None
    ) -> dw.DrawingElement:
        """Render the shape itself (without transforms).

        Args:
            state: State to render
            drawing: Optional Drawing for accessing defs
        """
        pass

    def render(
        self, state: State, drawing: dw.Drawing | None = None
    ) -> dw.DrawingElement:
        elem = self._render_core(state=state, drawing=drawing)

        # Apply clipping/masking before transforms (only if drawing is available)
        if drawing is not None:
            elem = self._apply_clipping_and_masking(elem, state, drawing)

            # Apply filter if specified
            elem = self._apply_filter(elem, state, drawing)

        transform = self._build_transform_string(state)
        needs_wrapper = not hasattr(elem, "args")

        if needs_wrapper or isinstance(elem, dw.elements.Group):
            kwargs = {}
            if transform:
                kwargs["transform"] = transform
            kwargs["opacity"] = str(state.opacity)
            mgroup = dw.Group(**kwargs)
            mgroup.append(elem)
            return mgroup

        _set_elem_attr(elem, "opacity", str(state.opacity))
        if transform:
            _set_elem_attr(elem, "transform", transform)

        return elem

    def _apply_clipping_and_masking(
        self, elem: dw.DrawingElement, state: State, drawing: dw.Drawing
    ) -> dw.DrawingElement:
        """Apply clip-path and mask to element based on state

        Handles:
        - Single clip (clip_state)
        - Multiple clips (clip_states) via nested groups
        - Single mask (mask_state)
        - Combination of clip + mask

        Args:
            elem: The rendered element to clip
            state: State containing clip/mask definitions
            drawing: Drawing for adding defs

        Returns:
            Element wrapped in groups with clipping/masking applied
        """

        result = elem

        # Normalize mask_state/mask_states to list
        if state.mask_state is not None:
            mask_states = [state.mask_state]
        elif state.mask_states is not None:
            mask_states = state.mask_states
        else:
            mask_states = []

        # Normalize clip_state/clip_states to list
        if state.clip_state is not None:
            clip_states = [state.clip_state]
        elif state.clip_states is not None:
            clip_states = state.clip_states
        else:
            clip_states = []

        # Apply masks first (innermost)
        for mask_state in mask_states:
            mask_id = self._create_mask_def(mask_state, drawing)
            masked_group = dw.Group(mask=f"url(#{mask_id})")
            masked_group.append(result)
            result = masked_group

        # Apply clips
        if len(clip_states) > 0:
            clip_id = self._create_clip_path_def(clip_states, drawing)
            clipped_group = dw.Group(clip_path=f"url(#{clip_id})")
            clipped_group.append(result)
            result = clipped_group

        return result

    def _create_clip_path_def(
        self, clip_states: list[State], drawing: dw.Drawing
    ) -> str:
        """Create ClipPath def from a state and add to drawing

        Args:
            clip_states: List of states defining the clip shape
            drawing: Drawing to add def to
        """
        import uuid

        # Generate unique ID
        clip_id = f"clip-{uuid.uuid4().hex[:8]}"

        # Create ClipPath container
        clip_path = dw.ClipPath(id=clip_id, clipPathUnits="userSpaceOnUse")

        for clip_state in clip_states:
            # For clipPaths, ensure the state has a fill (color doesn't matter for clipping)
            from svan2d.core.color import Color

            fill_color = getattr(clip_state, "fill_color", None)
            if fill_color is None or fill_color == Color.NONE:
                clip_state = replace(clip_state, fill_color=Color("#000000"))

            clip_elem = self._render_state_element(clip_state, drawing=drawing)

            transform = self._build_transform_string(clip_state)
            # Extract paths from group if needed (VertexRenderer returns a group)
            if isinstance(clip_elem, dw.Group) and hasattr(clip_elem, "children"):
                for child in clip_elem.children:
                    if transform:
                        _set_elem_attr(child, "transform", transform)
                    clip_path.append(child)
            else:
                if transform:
                    _set_elem_attr(clip_elem, "transform", transform)
                clip_path.append(clip_elem)

        # Add to drawing's defs
        drawing.append_def(clip_path)

        return clip_id

    def _create_mask_def(self, mask_state: State, drawing: dw.Drawing) -> str:
        """Create Mask def from a state and add to drawing

        Masks use opacity/grayscale for gradual transparency.
        White = fully visible, black = fully transparent.

        Args:
            mask_state: State defining the mask shape
            drawing: Drawing to add def to
        """
        import uuid

        # Generate unique ID
        mask_id = f"mask-{uuid.uuid4().hex[:8]}"

        # Create Mask container
        mask = dw.Mask(id=mask_id)

        # For masks, ensure the state has a fill (masks use white for visible areas)
        from svan2d.core.color import Color

        fill_color = getattr(mask_state, "fill_color", None)
        if fill_color is None or fill_color == Color.NONE:
            mask_state = replace(mask_state, fill_color=Color("#FFFFFF"))

        mask_elem = self._render_state_element(mask_state, drawing=drawing)

        # Extract paths from group if needed (VertexRenderer returns a group)
        if isinstance(mask_elem, dw.Group) and hasattr(mask_elem, "children"):
            elements = list(mask_elem.children)
        else:
            elements = [mask_elem]

        # Apply transforms and opacity directly
        transform = self._build_transform_string(mask_state)

        if transform or mask_state.opacity != 1.0:
            mask_group = dw.Group(opacity=mask_state.opacity)
            if transform:
                _set_elem_attr(mask_group, "transform", transform)
            for elem in elements:
                mask_group.append(elem)
            mask.append(mask_group)
        else:
            for elem in elements:
                mask.append(elem)

        # Add to drawing's defs
        drawing.append_def(mask)

        return mask_id

    def _apply_filter(
        self, elem: dw.DrawingElement, state: State, drawing: dw.Drawing
    ) -> dw.DrawingElement:
        """Apply filter to element based on state

        Args:
            elem: The rendered element to filter
            state: State containing filter definition
            drawing: Drawing for adding defs
        """
        if state.filter is None:
            return elem

        # Create filter def and add to drawing
        filter_id = self._create_filter_def(state.filter, drawing)

        # Apply filter to element
        _set_elem_attr(elem, "filter", f"url(#{filter_id})")

        return elem

    def _create_filter_def(self, filter_obj, drawing: dw.Drawing) -> str:
        """Create Filter def from a filter object and add to drawing

        Args:
            filter_obj: Filter object defining the filter effect
            drawing: Drawing to add def to
        """
        import uuid

        # Generate unique ID
        filter_id = f"filter-{uuid.uuid4().hex[:8]}"

        # Create Filter container
        filter_elem = dw.Filter(id=filter_id)

        # Handle composite filters (multiple filter items)
        from svan2d.primitive.effect.filter import CompositeFilter

        if isinstance(filter_obj, CompositeFilter):
            for sub_filter in filter_obj.filters:
                filter_item = sub_filter.to_drawsvg()
                filter_elem.append(filter_item)
        else:
            # Single filter
            filter_item = filter_obj.to_drawsvg()
            filter_elem.append(filter_item)

        # Add to drawing's defs
        drawing.append_def(filter_elem)

        return filter_id

    def _set_fill_and_stroke_kwargs(
        self, state: State, kwargs: dict, drawing: dw.Drawing | None = None
    ) -> None:
        """Helper to set fill and stroke attributes in kwargs dict

        Handles the standard priority order:
        - Fill: pattern → gradient → color → none
        - Stroke: pattern → gradient → color (if stroke_width > 0)

        Args:
            state: State containing fill/stroke attributes (typically ColorState)
            kwargs: Dictionary to populate with fill/stroke attributes
            drawing: Optional Drawing for pattern rendering
        """
        # Get fill/stroke attributes (these exist on ColorState subclass)
        fill_pattern = getattr(state, "fill_pattern", None)
        fill_gradient = getattr(state, "fill_gradient", None)
        fill_color = getattr(state, "fill_color", None)
        fill_opacity = getattr(state, "fill_opacity", 1.0)

        stroke_pattern = getattr(state, "stroke_pattern", None)
        stroke_gradient = getattr(state, "stroke_gradient", None)
        stroke_color = getattr(state, "stroke_color", None)
        stroke_width = getattr(state, "stroke_width", 0)
        stroke_opacity = getattr(state, "stroke_opacity", 1.0)

        # Check pattern first, then gradient, then color for fill
        if fill_pattern:
            kwargs["fill"] = fill_pattern.to_drawsvg(drawing)
        elif fill_gradient:
            kwargs["fill"] = fill_gradient.to_drawsvg()
        elif fill_color:
            kwargs["fill"] = fill_color.to_rgb_string()
            kwargs["fill_opacity"] = fill_opacity
        else:
            kwargs["fill"] = "none"

        # Check pattern first, then gradient, then color for stroke
        if stroke_pattern:
            kwargs["stroke"] = stroke_pattern.to_drawsvg(drawing)
            kwargs["stroke_width"] = stroke_width
        elif stroke_gradient:
            kwargs["stroke"] = stroke_gradient.to_drawsvg()
            kwargs["stroke_width"] = stroke_width
        elif stroke_color and stroke_width > 0:
            kwargs["stroke"] = stroke_color.to_rgb_string()
            kwargs["stroke_width"] = stroke_width
            kwargs["stroke_opacity"] = stroke_opacity

        # Non-scaling stroke: width stays in screen pixels regardless of transforms
        if getattr(state, "non_scaling_stroke", False):
            kwargs["vector_effect"] = "non-scaling-stroke"
