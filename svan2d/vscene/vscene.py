"""VScene - container for animated elements with frame generation."""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    TypeAlias,
    Union,
)

# Type alias for easing function
EasingFunc: TypeAlias = Callable[[float], float]

# Type aliases for camera animation functions
ScaleFunc: TypeAlias = Callable[[float], float]  # t -> scale
OffsetFunc: TypeAlias = Callable[[float], tuple[float, float]]  # t -> (x, y)
RotationFunc: TypeAlias = Callable[[float], float]  # t -> degrees

import drawsvg as dw

from svan2d.config import ConfigKey, get_config
from svan2d.core import Color, get_logger
from svan2d.core.point2d import Point2D
from svan2d.vscene.camera_state import CameraState

if TYPE_CHECKING:
    from svan2d.component.state.base import State
    from svan2d.velement import VElement, VElementGroup


# Type alias for any renderable element
RenderableElement = Union["VElement", "VElementGroup"]

logger = get_logger()


class VScene:
    """Manages multiple animated elements and generates frames for animation

    A scene coordinates the rendering of multiple elements at specific time points,
    with support for global transforms and styling.

    Configuration:
        Default values for width, height, and background can be customized via
        svan2d.toml configuration file. See svan2d.config documentation.
    """

    def __init__(
        self,
        width: float | None = None,
        height: float | None = None,
        background: Color | None = None,
        background_opacity: float | None = None,
        origin: Optional[Literal["center", "top-left"]] = None,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        scale: float = 1.0,
        rotation: float = 0.0,
        # Scene-level clipping/masking
        clip_state: Optional["State"] = None,
        mask_state: Optional["State"] = None,
        # Timeline easing
        timeline_easing: Optional[EasingFunc] = None,
    ) -> None:
        """Initialize a new scene with given dimensions and styling

        Args:
            width: Width of the scene in pixels (default: from config, 800)
            height: Height of the scene in pixels (default: from config, 800)
            background: Background color (default: from config, transparent)
            background_opacity: Opacity of the background 0.0-1.0 (default: from config, 1.0)
            origin: Coordinate origin (default: from config, "center")
            offset_x: Global X offset for entire scene
            offset_y: Global Y offset for entire scene
            scale: Global scale factor for entire scene
            rotation: Global rotation in degrees for entire scene
            clip_state: Optional clip path applied to entire scene
            mask_state: Optional mask applied to entire scene
            timeline_easing: Optional easing function applied to animation timeline.
                When set, warps the frame_time before rendering (e.g., in_out makes
                beginning and end of animation linger longer).
        """
        # Load config for defaults
        config = get_config()

        # Apply config defaults for None values
        _width: float = (
            width if width is not None else config.get(ConfigKey.SCENE_WIDTH, 800)
        )
        _height: float = (
            height if height is not None else config.get(ConfigKey.SCENE_HEIGHT, 800)
        )
        _background: Color | None = (
            background
            if background is not None
            else config.get(ConfigKey.SCENE_BACKGROUND_COLOR, Color.NONE)
        )
        _background_opacity: float = (
            background_opacity
            if background_opacity is not None
            else config.get(ConfigKey.SCENE_BACKGROUND_OPACITY, 1.0)
        )
        _origin: Literal["center", "top-left"] = (
            origin
            if origin is not None
            else config.get(ConfigKey.SCENE_ORIGIN_MODE, "center")
        )

        # Validation
        if _width <= 0 or _height <= 0:
            raise ValueError(
                f"Width and height must be positive, got {_width}x{_height}"
            )
        if not 0.0 <= _background_opacity <= 1.0:
            raise ValueError(
                f"background_opacity must be 0.0-1.0, got {_background_opacity}"
            )

        self.width = _width
        self.height = _height
        self.origin = _origin

        # Parse background color
        if isinstance(_background, str) and _background.lower() == "none":
            self.background: Color | None = None
        else:
            self.background = _background

        self.background_opacity = _background_opacity

        # Global transforms
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.scale = scale
        self.rotation = rotation

        # Scene-level clipping/masking
        self.clip_state = clip_state
        self.mask_state = mask_state

        # Timeline easing
        self.timeline_easing = timeline_easing

        # Elements list
        self.elements: List[RenderableElement] = []

        # Camera animation state
        self._camera_keystates: List[tuple[CameraState, float, Optional[Dict]]] = []
        self._camera_pending_easing: Optional[Dict[str, Callable[[float], float]]] = (
            None
        )

        # Camera animation functions (for function-based animate_camera)
        self._camera_scale_func: Optional[ScaleFunc] = None
        self._camera_offset_func: Optional[OffsetFunc] = None
        self._camera_rotation_func: Optional[RotationFunc] = None
        self._camera_func_easing: Optional[EasingFunc] = None

    # ========================================================================
    # Element Management
    # ========================================================================

    def add_element(self, element: RenderableElement) -> None:
        """Add an element or group to the scene

        Args:
            element: The element or group to add to the scene
        """
        self.elements.append(element)

    def add_elements(self, elements: Sequence[RenderableElement]) -> None:
        """Add multiple elements or groups to the scene

        Args:
            elements: List of elements or groups to add to the scene
        """
        self.elements.extend(elements)

    def remove_element(self, element: RenderableElement) -> bool:
        """Remove specific element from scene

        Args:
            element: The element to remove

        Returns:
            True if element was found and removed, False otherwise
        """
        try:
            self.elements.remove(element)
            return True
        except ValueError:
            return False

    def clear_elements(self) -> None:
        """Remove all elements from scene"""
        self.elements.clear()

    def element_count(self) -> int:
        """Get total number of elements in scene"""
        return len(self.elements)

    def animatable_element_count(self) -> int:
        """Get number of elements that have animation"""
        return sum(1 for e in self.elements if e.is_animatable())

    # ========================================================================
    # Camera Animation
    # ========================================================================

    def camera_keystate(self, state: CameraState, at: float) -> "VScene":
        """Add a camera keystate at the specified time.

        Args:
            state: CameraState for this keyframe
            at: Time position (0.0-1.0)

        Returns:
            self for chaining
        """
        # Attach pending easing to previous keystate
        if len(self._camera_keystates) > 0 and self._camera_pending_easing is not None:
            prev_state, prev_time, _ = self._camera_keystates[-1]
            self._camera_keystates[-1] = (
                prev_state,
                prev_time,
                self._camera_pending_easing,
            )
            self._camera_pending_easing = None

        self._camera_keystates.append((state, at, None))
        return self

    def camera_transition(
        self,
        easing_dict: Optional[Dict[str, Callable[[float], float]]] = None,
    ) -> "VScene":
        """Configure the transition between the previous and next camera keystate.

        Args:
            easing_dict: Per-field easing functions for this segment

        Returns:
            self for chaining
        """
        if len(self._camera_keystates) == 0:
            raise ValueError(
                "camera_transition() cannot be called before camera_keystate()"
            )

        if self._camera_pending_easing is None:
            self._camera_pending_easing = easing_dict or {}
        elif easing_dict:
            self._camera_pending_easing = {**self._camera_pending_easing, **easing_dict}

        return self

    def animate_camera(
        self,
        scale: Optional[Union[tuple[float, float], ScaleFunc]] = None,
        offset: Optional[
            Union[tuple[tuple[float, float], tuple[float, float]], OffsetFunc]
        ] = None,
        rotation: Optional[Union[tuple[float, float], RotationFunc]] = None,
        pivot: Optional[tuple[float, float]] = None,
        easing: Optional[Callable[[float], float]] = None,
    ) -> "VScene":
        """Convenience method for simple 2-point camera animation.

        Supports both tuple-based (start, end) values and function-based values.
        Functions receive eased_t (0.0-1.0) and return the value at that time.

        Args:
            scale: Either (start_scale, end_scale) tuple, or function(eased_t) -> float
            offset: Either ((start_x, start_y), (end_x, end_y)) tuple,
                    or function(eased_t) -> (x, y)
            rotation: Either (start_deg, end_deg) tuple, or function(eased_t) -> degrees
            pivot: (pivot_x, pivot_y) zoom/rotation center point
            easing: Easing function applied to t before passing to any functions
                    or interpolation

        Returns:
            self for chaining

        Example:
            # Tuple-based (original behavior)
            scene.animate_camera(scale=(1.0, 0.5), easing=easing.in_out)

            # Function-based (new behavior)
            import math
            scene.animate_camera(
                scale=lambda t: 1.0 + 0.5 * math.sin(t * 2 * math.pi),
                offset=lambda t: (100 * t, 50 * math.sin(t * math.pi)),
                rotation=lambda t: 360 * t * t,
                easing=easing.in_out
            )
        """
        # Clear previous function settings
        self._camera_scale_func = None
        self._camera_offset_func = None
        self._camera_rotation_func = None
        self._camera_func_easing = easing

        pivot_pt = Point2D(pivot[0], pivot[1]) if pivot else Point2D(0, 0)

        # Determine if using functions or tuples for each parameter
        scale_is_func = callable(scale)
        offset_is_func = callable(offset)
        rotation_is_func = callable(rotation)

        # Store functions if provided
        if scale_is_func:
            self._camera_scale_func = scale
        if offset_is_func:
            self._camera_offset_func = offset
        if rotation_is_func:
            self._camera_rotation_func = rotation

        # Determine start/end values (use defaults for function-based params)
        start_scale = 1.0 if scale_is_func or scale is None else scale[0]
        end_scale = 1.0 if scale_is_func or scale is None else scale[1]

        start_offset = (
            Point2D(0, 0)
            if offset_is_func or offset is None
            else Point2D(offset[0][0], offset[0][1])
        )
        end_offset = (
            Point2D(0, 0)
            if offset_is_func or offset is None
            else Point2D(offset[1][0], offset[1][1])
        )

        start_rotation = 0.0 if rotation_is_func or rotation is None else rotation[0]
        end_rotation = 0.0 if rotation_is_func or rotation is None else rotation[1]

        start = CameraState(
            scale=start_scale,
            pos=start_offset,
            rotation=start_rotation,
            pivot=pivot_pt,
        )
        end = CameraState(
            scale=end_scale,
            pos=end_offset,
            rotation=end_rotation,
            pivot=pivot_pt,
        )

        easing_dict = None
        if easing is not None:
            easing_dict = {"scale": easing, "pos": easing, "rotation": easing}

        return (
            self.camera_keystate(start, at=0.0)
            .camera_transition(easing_dict=easing_dict)
            .camera_keystate(end, at=1.0)
        )

    def _get_camera_state_at_time(self, frame_time: float) -> CameraState:
        """Get interpolated camera state with visually linear panning.

        Uses custom interpolation that compensates pos for scale changes,
        ensuring camera movement appears linear on screen regardless of zoom.
        """
        from svan2d.transition import easing as easing_module

        if len(self._camera_keystates) < 2:
            if len(self._camera_keystates) == 1:
                return self._camera_keystates[0][0]
            # No camera animation - return static properties
            return CameraState(
                scale=self.scale,
                rotation=self.rotation,
                pos=Point2D(self.offset_x, self.offset_y),
            )

        # Find the segment containing frame_time
        keystates = self._camera_keystates

        # Handle boundary cases
        # If functions are set, apply them even at boundaries
        has_funcs = (
            self._camera_scale_func is not None
            or self._camera_offset_func is not None
            or self._camera_rotation_func is not None
        )

        if frame_time <= keystates[0][1]:
            if not has_funcs:
                return keystates[0][0]
            # Apply functions at boundary
            base_state = keystates[0][0]
            return self._apply_camera_functions(base_state, frame_time)

        if frame_time >= keystates[-1][1]:
            if not has_funcs:
                return keystates[-1][0]
            # Apply functions at boundary
            base_state = keystates[-1][0]
            return self._apply_camera_functions(base_state, frame_time)

        # Find segment
        start_state, start_time, easing_dict = keystates[0]
        end_state, end_time, _ = keystates[1]

        for i in range(len(keystates) - 1):
            if keystates[i][1] <= frame_time <= keystates[i + 1][1]:
                start_state, start_time, easing_dict = keystates[i]
                end_state, end_time, _ = keystates[i + 1]
                break

        # Compute local t (0-1 within segment)
        if end_time == start_time:
            local_t = 0.0
        else:
            local_t = (frame_time - start_time) / (end_time - start_time)

        # Get easing functions
        scale_easing = (
            easing_dict.get("scale", easing_module.linear)
            if easing_dict
            else easing_module.linear
        )
        pos_easing = (
            easing_dict.get("pos", easing_module.linear)
            if easing_dict
            else easing_module.linear
        )
        rotation_easing = (
            easing_dict.get("rotation", easing_module.linear)
            if easing_dict
            else easing_module.linear
        )

        # Apply easing
        scale_t = scale_easing(local_t)
        pos_t = pos_easing(local_t)
        rotation_t = rotation_easing(local_t)

        # CameraState fields are guaranteed non-None after __post_init__
        assert start_state.scale is not None and end_state.scale is not None
        assert start_state.rotation is not None and end_state.rotation is not None
        assert start_state.pos is not None and end_state.pos is not None
        assert start_state.pivot is not None and end_state.pivot is not None
        assert start_state.opacity is not None and end_state.opacity is not None

        # Interpolate scale and rotation normally
        interp_scale = (
            start_state.scale + (end_state.scale - start_state.scale) * scale_t
        )
        interp_rotation = (
            start_state.rotation
            + (end_state.rotation - start_state.rotation) * rotation_t
        )

        # For visually linear panning: interpolate "visual target" (pos * scale)
        # then derive world pos from that
        start_visual = Point2D(
            start_state.pos.x * start_state.scale, start_state.pos.y * start_state.scale
        )
        end_visual = Point2D(
            end_state.pos.x * end_state.scale, end_state.pos.y * end_state.scale
        )

        # Interpolate visual target linearly (using pos easing)
        interp_visual = Point2D(
            start_visual.x + (end_visual.x - start_visual.x) * pos_t,
            start_visual.y + (end_visual.y - start_visual.y) * pos_t,
        )

        # Convert back to world pos
        if interp_scale != 0:
            interp_pos = Point2D(
                interp_visual.x / interp_scale, interp_visual.y / interp_scale
            )
        else:
            interp_pos = Point2D(0, 0)

        # Interpolate pivot (simple linear)
        interp_pivot = Point2D(
            start_state.pivot.x + (end_state.pivot.x - start_state.pivot.x) * local_t,
            start_state.pivot.y + (end_state.pivot.y - start_state.pivot.y) * local_t,
        )

        # Interpolate opacity
        interp_opacity = (
            start_state.opacity + (end_state.opacity - start_state.opacity) * local_t
        )

        # Override with function-based values if functions are set
        if (
            self._camera_scale_func is not None
            or self._camera_offset_func is not None
            or self._camera_rotation_func is not None
        ):
            # Apply function easing to frame_time (not local_t)
            func_easing = self._camera_func_easing or easing_module.linear
            eased_frame_time = func_easing(frame_time)

            if self._camera_scale_func is not None:
                interp_scale = self._camera_scale_func(eased_frame_time)

            if self._camera_rotation_func is not None:
                interp_rotation = self._camera_rotation_func(eased_frame_time)

            if self._camera_offset_func is not None:
                ox, oy = self._camera_offset_func(eased_frame_time)
                interp_pos = Point2D(ox, oy)

        return CameraState(
            scale=interp_scale,
            rotation=interp_rotation,
            pos=interp_pos,
            pivot=interp_pivot,
            opacity=interp_opacity,
        )

    def _apply_camera_functions(
        self, base_state: CameraState, frame_time: float
    ) -> CameraState:
        """Apply camera functions to a base state at given frame_time.

        Helper method for applying function-based camera values at boundary cases.

        Args:
            base_state: The base CameraState to modify
            frame_time: Time to pass to functions (0.0-1.0)

        Returns:
            CameraState with function values applied
        """
        from svan2d.transition import easing as easing_module

        func_easing = self._camera_func_easing or easing_module.linear
        eased_frame_time = func_easing(frame_time)

        scale = base_state.scale
        rotation = base_state.rotation
        pos = base_state.pos

        if self._camera_scale_func is not None:
            scale = self._camera_scale_func(eased_frame_time)

        if self._camera_rotation_func is not None:
            rotation = self._camera_rotation_func(eased_frame_time)

        if self._camera_offset_func is not None:
            ox, oy = self._camera_offset_func(eased_frame_time)
            pos = Point2D(ox, oy)

        return CameraState(
            scale=scale,
            rotation=rotation,
            pos=pos,
            pivot=base_state.pivot,
            opacity=base_state.opacity,
        )

    def _build_camera_transform(self, state: CameraState, render_scale: float) -> str:
        """Build SVG transform string from camera state with pivot support.

        Args:
            state: CameraState with transform values
            render_scale: Additional scale factor for rendering

        Returns:
            SVG transform string
        """
        # CameraState fields are guaranteed non-None after __post_init__
        assert (
            state.scale is not None
            and state.pivot is not None
            and state.rotation is not None
        )

        parts = []
        total_scale = state.scale * render_scale

        has_pivot = state.pivot.x != 0 or state.pivot.y != 0
        has_transform = total_scale != 1.0 or state.rotation != 0

        # Pivot: translate to pivot point, apply transforms, translate back
        if has_pivot and has_transform:
            parts.append(f"translate({state.pivot.x},{state.pivot.y})")

        if total_scale != 1.0:
            parts.append(f"scale({total_scale})")

        if state.rotation != 0:
            parts.append(f"rotate({state.rotation})")

        if has_pivot and has_transform:
            parts.append(f"translate({-state.pivot.x},{-state.pivot.y})")

        # Camera position LAST (world space - applied first in SVG right-to-left order)
        if state.x != 0 or state.y != 0:
            parts.append(f"translate({-state.x},{-state.y})")

        return " ".join(parts)

    # ========================================================================
    # Rendering
    # ========================================================================

    def to_drawing(
        self,
        frame_time: float = 0.0,
        render_scale: float = 1.0,
        width: float | None = None,
        height: float | None = None,
    ) -> dw.Drawing:
        """Render the scene as a drawsvg Drawing object at specified time.

        Useful for video encoding or when you need the Drawing object
        directly without converting to SVG string.

        Args:
            frame_time: Time point to render (0.0 to 1.0)
            render_scale: Additional scale factor for rendering (multiplies scene scale)
            width: Optional width override (in pixels)
            height: Optional height override (in pixels)

        Returns:
            dw.Drawing object

        Raises:
            ValueError: If frame_time is outside [0.0, 1.0]
        """
        # Validation
        if not 0.0 <= frame_time <= 1.0:
            raise ValueError(
                f"frame_time must be between 0.0 and 1.0, got {frame_time}"
            )

        # Apply timeline easing if set
        if self.timeline_easing is not None:
            frame_time = self.timeline_easing(frame_time)

        # Calculate final dimensions
        ww = width if width is not None else render_scale * self.width
        hh = height if height is not None else render_scale * self.height

        drawing = dw.Drawing(ww, hh, origin=self.origin)

        # Add background
        if self.background is not None and self.background_opacity > 0.0:
            # Calculate background position based on origin
            if self.origin == "center":
                bg_x, bg_y = -ww / 2, -hh / 2
            else:  # top-left
                bg_x, bg_y = 0, 0

            drawing.append(
                dw.Rectangle(
                    bg_x,
                    bg_y,
                    ww,
                    hh,
                    fill=self.background.to_rgb_string(),
                    fill_opacity=self.background_opacity,
                )
            )

        # Create global transform group (use animated camera if available)
        camera_state = self._get_camera_state_at_time(frame_time)
        transform = self._build_camera_transform(camera_state, render_scale)
        group = dw.Group(transform=transform) if transform else dw.Group()

        # Pre-compute interpolated states once for all elements (avoid double interpolation)
        element_states = []
        for element in self.elements:
            if hasattr(element, "get_frame"):
                state = element.get_frame(frame_time)
                element_states.append((element, state))
            else:
                element_states.append((element, None))

        # Sort by z_index using pre-computed states
        def get_z_index(elem_state_tuple) -> float:
            _, state = elem_state_tuple
            return state.z_index if state is not None else 0.0

        sorted_element_states = sorted(element_states, key=get_z_index)

        # Render elements using cached states
        for element, state in sorted_element_states:
            if state is not None:
                rendered = element.render_state(state, drawing=drawing)
                if rendered is not None:
                    group.append(rendered)

        # Apply scene-level clipping/masking
        if self.clip_state or self.mask_state:
            group = self._apply_scene_clipping(group, drawing)

        drawing.append(group)
        return drawing

    def to_svg(
        self,
        frame_time: float = 0.0,
        render_scale: float = 1.0,
        width: float | None = None,
        height: float | None = None,
        filename: str | None = None,
        log: bool = True,
    ) -> str:
        """Render the scene to SVG string at specified time.

        Args:
            frame_time: Time point to render (0.0 to 1.0)
            render_scale: Additional scale factor for rendering
            width: Optional width override (in pixels)
            height: Optional height override (in pixels)
            filename: Optional filename to save SVG to
            log: Whether to log the save operation

        Returns:
            SVG string

        Raises:
            ValueError: If frame_time is outside [0.0, 1.0]
        """
        drawing = self.to_drawing(
            frame_time=frame_time,
            render_scale=render_scale,
            width=width,
            height=height,
        )

        svg_string: str = drawing.as_svg()  # type: ignore[assignment]

        if filename:
            drawing.save_svg(filename)

        return svg_string

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _build_transform(self, render_scale: float) -> str:
        """Build SVG transform string from scene transforms

        Args:
            render_scale: Additional scale factor for rendering

        Returns:
            SVG transform string, or empty string if no transforms needed
        """
        transforms = []

        # Combine scene scale with render scale
        total_scale = self.scale * render_scale
        if total_scale != 1.0:
            transforms.append(f"scale({total_scale})")

        # Add rotation if present
        if self.rotation != 0.0:
            transforms.append(f"rotate({self.rotation})")

        # Add translation if present
        if self.offset_x != 0.0 or self.offset_y != 0.0:
            transforms.append(f"translate({self.offset_x},{self.offset_y})")

        return " ".join(transforms)

    def _apply_scene_clipping(self, group: dw.Group, drawing: dw.Drawing) -> dw.Group:
        """Apply scene-level clip/mask to root group

        Uses the same clipping logic as Renderer._apply_clipping_and_masking
        but at the scene level.

        Args:
            group: The group containing all scene elements
            drawing: Drawing for adding defs

        Returns:
            Group wrapped in clip/mask groups if needed
        """
        import uuid

        from svan2d.component import get_renderer_instance_for_state

        result = group

        # Apply mask first (innermost)
        if self.mask_state is not None:
            mask_id = f"mask-{uuid.uuid4().hex[:8]}"
            mask = dw.Mask(id=mask_id)

            # Render the mask shape
            renderer = get_renderer_instance_for_state(self.mask_state)
            mask_elem = renderer._render_core(self.mask_state, drawing=drawing)

            # Apply transforms and opacity
            transforms = []
            if self.mask_state.x != 0 or self.mask_state.y != 0:
                transforms.append(f"translate({self.mask_state.x},{self.mask_state.y})")
            if self.mask_state.rotation != 0:
                transforms.append(f"rotate({self.mask_state.rotation})")
            if self.mask_state.scale != 1.0:
                transforms.append(f"scale({self.mask_state.scale})")

            mask_group = dw.Group(opacity=self.mask_state.opacity)
            if transforms:
                mask_group.args["transform"] = " ".join(transforms)
            mask_group.append(mask_elem)
            mask.append(mask_group)

            drawing.append_def(mask)

            masked_group = dw.Group(mask=f"url(#{mask_id})")
            masked_group.append(result)
            result = masked_group

        # Apply clip
        if self.clip_state is not None:
            clip_id = f"clip-{uuid.uuid4().hex[:8]}"
            clip_path = dw.ClipPath(id=clip_id)

            # Render the clip shape
            renderer = get_renderer_instance_for_state(self.clip_state)
            clip_elem = renderer._render_core(self.clip_state, drawing=drawing)

            # Apply clip's own transforms
            if (
                self.clip_state.x != 0
                or self.clip_state.y != 0
                or self.clip_state.rotation != 0
                or self.clip_state.scale != 1.0
            ):
                transforms = []
                if self.clip_state.x != 0 or self.clip_state.y != 0:
                    transforms.append(
                        f"translate({self.clip_state.x},{self.clip_state.y})"
                    )
                if self.clip_state.rotation != 0:
                    transforms.append(f"rotate({self.clip_state.rotation})")
                if self.clip_state.scale != 1.0:
                    transforms.append(f"scale({self.clip_state.scale})")
                clip_group = dw.Group(transform=" ".join(transforms))
                clip_group.append(clip_elem)
                clip_path.append(clip_group)
            else:
                clip_path.append(clip_elem)

            drawing.append_def(clip_path)

            clipped_group = dw.Group(clip_path=f"url(#{clip_id})")
            clipped_group.append(result)
            result = clipped_group

        return result

    def get_animation_time_range(self) -> tuple[float, float]:
        """Get the time range covered by all elements

        Returns the minimum start time and maximum end time across all
        elements that have keystates.

        Returns:
            Tuple of (min_time, max_time). Returns (0.0, 1.0) if no elements have keystates.
        """
        if not self.elements:
            return (0.0, 1.0)

        times: List[float] = []
        for element in self.elements:
            keystates = getattr(element, "_keystates_list", None)
            if keystates and isinstance(keystates, list) and len(keystates) > 0:
                times.append(keystates[0].time)  # First keystate time
                times.append(keystates[-1].time)  # Last keystate time

        if not times:
            return (0.0, 1.0)

        return (min(times), max(times))

    # ========================================================================
    # Convenience Attributes
    # ========================================================================

    @property
    def dimensions(self) -> tuple[float, float]:
        """Get scene dimensions as (width, height)"""
        return (self.width, self.height)

    @property
    def aspect_ratio(self) -> float:
        """Get scene aspect ratio (width / height)"""
        return self.width / self.height

    # ========================================================================
    # Jupyter Notebook Display
    # ========================================================================

    def _repr_svg_(self):
        """Display in Jupyter notebook (auto-called by Jupyter)."""
        from svan2d.vscene.preview import PreviewRenderer

        return PreviewRenderer(self).repr_svg()

    def display_inline(self, frame_time: float = 0.0):
        """Display inline in the Jupyter web page.

        Args:
            frame_time: Time point to render (0.0 to 1.0)

        Returns:
            JupyterSvgInline object that displays in notebooks
        """
        from svan2d.vscene.preview import PreviewRenderer

        return PreviewRenderer(self).display_inline(frame_time)

    def display_iframe(self, frame_time: float = 0.0):
        """Display within an iframe in the Jupyter web page.

        Args:
            frame_time: Time point to render (0.0 to 1.0)

        Returns:
            JupyterSvgFrame object that displays in notebooks
        """
        from svan2d.vscene.preview import PreviewRenderer

        return PreviewRenderer(self).display_iframe(frame_time)

    def display_image(self, frame_time: float = 0.0):
        """Display within an img tag in the Jupyter web page.

        Args:
            frame_time: Time point to render (0.0 to 1.0)

        Returns:
            JupyterSvgImage object that displays in notebooks
        """
        from svan2d.vscene.preview import PreviewRenderer

        return PreviewRenderer(self).display_image(frame_time)

    def preview_grid(self, num_frames: int = 10, scale: float = 1.0):
        """Preview animation by showing all frames in a grid layout.

        Useful for quickly checking animations in Jupyter without video export.
        Shows all frames at once for easy visual comparison.

        Args:
            num_frames: Number of frames to display (default: 10)
            scale: Scale factor for frame size, e.g. 0.5 for half size (default: 1.0)

        Returns:
            HTML object that displays in Jupyter notebooks
        """
        from svan2d.vscene.preview import PreviewRenderer

        return PreviewRenderer(self).preview_grid(num_frames, scale)

    def preview_animation(self, num_frames: int = 10, play_interval_ms: int = 100):
        """Preview animation with interactive controls (play/pause, slider, prev/next).

        Useful for checking animations in Jupyter without video export.
        Shows one frame at a time with playback controls.

        Args:
            num_frames: Number of frames to display (default: 10)
            play_interval_ms: Milliseconds between frames when playing (default: 100)

        Returns:
            HTML object that displays in Jupyter notebooks
        """
        from svan2d.vscene.preview import PreviewRenderer

        return PreviewRenderer(self).preview_animation(num_frames, play_interval_ms)

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"VScene(width={self.width}, height={self.height}, "
            f"elements={len(self.elements)}, "
            f"animatable={self.animatable_element_count()})"
        )
