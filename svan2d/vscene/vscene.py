"""VScene - container for animated elements with frame generation."""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Callable,
    Sequence,
    TypeAlias,
)

import drawsvg as dw

from svan2d.config import ConfigKey, get_config
from svan2d.velement.base_velement import _UNSET, _Unset
from svan2d.core import Color, get_logger
from svan2d.core.enums import Origin
from svan2d.core.point2d import Point2D
from svan2d.vscene import camera as camera_mod
from svan2d.vscene import rendering as rendering_mod

# Type alias for easing function
EasingFunc: TypeAlias = Callable[[float], float]

# Type aliases for camera animation functions
ScaleFunc: TypeAlias = Callable[[float], float]  # t -> scale
OffsetFunc: TypeAlias = Callable[[float], Point2D]  # t -> Point2D
RotationFunc: TypeAlias = Callable[[float], float]  # t -> degrees
from svan2d.vscene.camera_state import CameraState

if TYPE_CHECKING:
    from svan2d.primitive.state.base import State
    from svan2d.velement import VElement, VElementGroup


# Type alias for any renderable element
RenderableElement: TypeAlias = "VElement | VElementGroup"

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
        origin: Origin | None = None,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        scale: float = 1.0,
        rotation: float = 0.0,
        # Scene-level clipping/masking
        clip_state: "State | None" = None,
        mask_state: "State | None" = None,
        # Timeline easing
        timeline_easing: EasingFunc | None = None,
        reverse: bool = False,
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
        _origin: Origin = (
            origin
            if origin is not None
            else Origin(config.get(ConfigKey.SCENE_ORIGIN_MODE, "center"))
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

        # Reverse playback
        self.reverse = reverse

        # Elements list
        self.elements: list[RenderableElement] = []

        # Camera animation state
        self._camera_keystates: list[tuple[CameraState, float, dict | None]] = []
        self._camera_pending_easing: dict[str, Callable[[float], float]] | None = None

        # Camera animation functions (for function-based animate_camera)
        self._camera_scale_func: ScaleFunc | None = None
        self._camera_offset_func: OffsetFunc | None = None
        self._camera_rotation_func: RotationFunc | None = None
        self._camera_func_easing: EasingFunc | None = None

    def _replace(
        self,
        *,
        elements: list[RenderableElement] | None = None,
        camera_keystates: list[tuple[CameraState, float, dict | None]] | None = None,
        camera_pending_easing: (
            dict[str, Callable[[float], float]] | None | _Unset
        ) = _UNSET,
        camera_scale_func: ScaleFunc | None | _Unset = _UNSET,
        camera_offset_func: OffsetFunc | None | _Unset = _UNSET,
        camera_rotation_func: RotationFunc | None | _Unset = _UNSET,
        camera_func_easing: EasingFunc | None | _Unset = _UNSET,
    ) -> "VScene":
        """Return a new VScene with specified attributes replaced."""
        new = VScene.__new__(VScene)
        # Copy all base attributes
        new.width = self.width
        new.height = self.height
        new.origin = self.origin
        new.background = self.background
        new.background_opacity = self.background_opacity
        new.offset_x = self.offset_x
        new.offset_y = self.offset_y
        new.scale = self.scale
        new.rotation = self.rotation
        new.clip_state = self.clip_state
        new.mask_state = self.mask_state
        new.timeline_easing = self.timeline_easing
        new.reverse = self.reverse

        # Replace specified attributes
        new.elements = elements if elements is not None else self.elements.copy()
        new._camera_keystates = (
            camera_keystates
            if camera_keystates is not None
            else self._camera_keystates.copy()
        )
        new._camera_pending_easing = (
            self._camera_pending_easing
            if camera_pending_easing is _UNSET
            else camera_pending_easing
        )
        new._camera_scale_func = (
            self._camera_scale_func
            if camera_scale_func is _UNSET
            else camera_scale_func
        )
        new._camera_offset_func = (
            self._camera_offset_func
            if camera_offset_func is _UNSET
            else camera_offset_func
        )
        new._camera_rotation_func = (
            self._camera_rotation_func
            if camera_rotation_func is _UNSET
            else camera_rotation_func
        )
        new._camera_func_easing = (
            self._camera_func_easing
            if camera_func_easing is _UNSET
            else camera_func_easing
        )
        return new

    # ========================================================================
    # Element Management
    # ========================================================================

    def add_element(self, element: RenderableElement) -> "VScene":
        """Add an element or group to the scene. Returns new VScene.

        Args:
            element: The element or group to add to the scene

        Returns:
            New VScene with the element added
        """
        return self._replace(elements=self.elements + [element])

    def add_elements(self, elements: Sequence[RenderableElement]) -> "VScene":
        """Add multiple elements or groups to the scene. Returns new VScene.

        Args:
            elements: List of elements or groups to add to the scene

        Returns:
            New VScene with elements added
        """
        return self._replace(elements=self.elements + list(elements))

    def remove_element(self, element: RenderableElement) -> "VScene":
        """Remove specific element from scene. Returns new VScene.

        Args:
            element: The element to remove

        Returns:
            New VScene with the element removed

        Raises:
            ValueError: If element not found in scene
        """
        if element not in self.elements:
            raise ValueError("Element not found in scene")
        return self._replace(elements=[e for e in self.elements if e is not element])

    def clear_elements(self) -> "VScene":
        """Remove all elements from scene. Returns new VScene."""
        return self._replace(elements=[])

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
        """Add a camera keystate at the specified time. Returns new VScene.

        Args:
            state: CameraState for this keyframe
            at: Time position (0.0-1.0)

        Returns:
            New VScene with camera keystate added
        """
        new_keystates = self._camera_keystates.copy()
        new_pending = self._camera_pending_easing

        # Attach pending easing to previous keystate
        if len(new_keystates) > 0 and new_pending is not None:
            prev_state, prev_time, _ = new_keystates[-1]
            new_keystates[-1] = (prev_state, prev_time, new_pending)
            new_pending = None

        new_keystates.append((state, at, None))
        return self._replace(
            camera_keystates=new_keystates, camera_pending_easing=new_pending
        )

    def camera_transition(
        self,
        easing_dict: dict[str, Callable[[float], float]] | None = None,
    ) -> "VScene":
        """Configure the transition between the previous and next camera keystate.
        Returns new VScene.

        Args:
            easing_dict: Per-field easing functions for this segment

        Returns:
            New VScene with camera transition configured
        """
        if len(self._camera_keystates) == 0:
            raise ValueError(
                "camera_transition() cannot be called before camera_keystate()"
            )

        if self._camera_pending_easing is None:
            new_pending = easing_dict or {}
        elif easing_dict:
            new_pending = {**self._camera_pending_easing, **easing_dict}
        else:
            new_pending = self._camera_pending_easing

        return self._replace(camera_pending_easing=new_pending)

    def animate_camera(
        self,
        scale: tuple[float, float] | ScaleFunc | None = None,
        offset: tuple[Point2D, Point2D] | OffsetFunc | None = None,
        rotation: tuple[float, float] | RotationFunc | None = None,
        pivot: Point2D | None = None,
        easing: Callable[[float], float] | None = None,
    ) -> "VScene":
        """Convenience method for simple 2-point camera animation. Returns new VScene.

        Supports both tuple-based (start, end) values and function-based values.
        Functions receive eased_t (0.0-1.0) and return the value at that time.

        Args:
            scale: Either (start_scale, end_scale) tuple, or function(eased_t) -> float
            offset: Either (start_point, end_point) tuple of Point2D,
                    or function(eased_t) -> Point2D
            rotation: Either (start_deg, end_deg) tuple, or function(eased_t) -> degrees
            pivot: Zoom/rotation center point (Point2D).
            easing: Easing function applied to t before passing to any functions
                    or interpolation

        Returns:
            New VScene with camera animation configured
        """
        pivot_pt = pivot if pivot else Point2D(0, 0)

        # Determine if using functions or tuples for each parameter
        scale_is_func = callable(scale)
        offset_is_func = callable(offset)
        rotation_is_func = callable(rotation)

        # Build function settings
        new_scale_func = scale if scale_is_func else None
        new_offset_func = offset if offset_is_func else None
        new_rotation_func = rotation if rotation_is_func else None

        # Determine start/end values (use defaults for function-based params)
        start_scale = 1.0 if scale_is_func or scale is None else scale[0]
        end_scale = 1.0 if scale_is_func or scale is None else scale[1]

        start_offset = Point2D(0, 0) if offset_is_func or offset is None else offset[0]
        end_offset = Point2D(0, 0) if offset_is_func or offset is None else offset[1]

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

        # Chain camera methods and set function values
        result = (
            self.camera_keystate(start, at=0.0)
            .camera_transition(easing_dict=easing_dict)
            .camera_keystate(end, at=1.0)
        )

        # Apply function settings using _replace
        return result._replace(
            camera_scale_func=new_scale_func,
            camera_offset_func=new_offset_func,
            camera_rotation_func=new_rotation_func,
            camera_func_easing=easing,
        )

    def _has_camera_funcs(self) -> bool:
        return camera_mod.has_camera_funcs(
            self._camera_scale_func,
            self._camera_offset_func,
            self._camera_rotation_func,
        )

    def _get_camera_state_at_time(self, frame_time: float) -> CameraState:
        """Get interpolated camera state at given time."""
        return camera_mod.get_camera_state_at_time(
            frame_time,
            self._camera_keystates,
            self._camera_scale_func,
            self._camera_offset_func,
            self._camera_rotation_func,
            self._camera_func_easing,
            self.scale,
            self.rotation,
            self.offset_x,
            self.offset_y,
        )

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

        # Apply reverse if set
        if self.reverse:
            frame_time = 1.0 - frame_time

        # Apply timeline easing if set
        if self.timeline_easing is not None:
            frame_time = self.timeline_easing(frame_time)

        # Calculate final dimensions
        ww = width if width is not None else render_scale * self.width
        hh = height if height is not None else render_scale * self.height

        drawing = dw.Drawing(ww, hh, origin=self.origin)

        # Add background
        if self.background is not None and self.background_opacity > 0.0:
            if self.origin == Origin.CENTER:
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
        needs_centering = self.origin != Origin.CENTER and self._camera_offset_func is not None
        vp_w, vp_h = (ww, hh) if needs_centering else (0.0, 0.0)
        transform = camera_mod.build_camera_transform(camera_state, render_scale, vp_w, vp_h)
        group = dw.Group(transform=transform) if transform else dw.Group()

        # Pre-compute interpolated states once for all elements
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
            group = rendering_mod.apply_scene_clipping(
                group, drawing, self.clip_state, self.mask_state
            )

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
        """Build SVG transform string from scene transforms."""

        return rendering_mod.build_scene_transform(
            self.scale, self.rotation, self.offset_x, self.offset_y, render_scale
        )

    def get_animation_time_range(self) -> tuple[float, float]:
        """Get the time range covered by all elements

        Returns the minimum start time and maximum end time across all
        elements that have keystates.

        Returns:
            Tuple of (min_time, max_time). Returns (0.0, 1.0) if no elements have keystates.
        """
        if not self.elements:
            return (0.0, 1.0)

        times: list[float] = []
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
