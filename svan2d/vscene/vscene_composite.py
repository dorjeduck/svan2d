"""VSceneComposite - spatial composition of multiple scenes.

Enables stacking multiple VScenes horizontally or vertically with automatic
scaling. Composites are nestable and work seamlessly with VSceneSequence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal, Optional, Union

import drawsvg as dw

from svan2d.core import get_logger

if TYPE_CHECKING:
    from svan2d.vscene.vscene import VScene
    from svan2d.vscene.vscene_sequence import VSceneSequence

logger = get_logger()

# Type alias for composable scene types
ComposableScene = Union["VScene", "VSceneSequence", "VSceneComposite"]


class VSceneComposite:
    """Spatial composition of multiple scenes.

    VSceneComposite stacks multiple scenes horizontally or vertically with
    automatic scaling to align dimensions. Scenes maintain aspect ratio.

    Example:
        # Horizontal stack (scenes scaled to match max height)
        row = VSceneComposite([scene1, scene2, scene3], direction="horizontal")

        # Vertical stack (scenes scaled to match max width)
        column = VSceneComposite([scene1, scene2, scene3], direction="vertical")

        # Nesting - create a grid
        row1 = VSceneComposite([scene1, scene2], direction="horizontal")
        row2 = VSceneComposite([scene3, scene4], direction="horizontal")
        grid = VSceneComposite([row1, row2], direction="vertical")

        # Export via VSceneExporter
        VSceneExporter(grid).to_mp4("grid.mp4", total_frames=60)
    """

    def __init__(
        self,
        scenes: List[ComposableScene],
        direction: Literal["horizontal", "vertical"] = "horizontal",
        gap: float = 0.0,
        origin: Optional[Literal["center", "top-left"]] = None,
    ) -> None:
        """Initialize a composite of scenes.

        Args:
            scenes: List of VScene, VSceneSequence, or VSceneComposite to compose
            direction: Stack direction - "horizontal" or "vertical"
            gap: Gap between scenes in pixels (default: 0.0)
            origin: Override origin mode (default: use first scene's origin)

        Raises:
            ValueError: If scenes list is empty or direction is invalid
        """
        if not scenes:
            raise ValueError("Cannot create composite with empty scenes list")

        if direction not in ("horizontal", "vertical"):
            raise ValueError(
                f"direction must be 'horizontal' or 'vertical', got '{direction}'"
            )

        self._scenes = list(scenes)
        self._direction: Literal["horizontal", "vertical"] = direction
        self._gap = gap
        self._origin_override = origin

        # Compute scales and dimensions
        self._scales: List[float] = []
        self._total_width: float = 0.0
        self._total_height: float = 0.0
        self._compute_layout()

    @staticmethod
    def _round_to_even(value: float) -> float:
        """Round a value to the nearest even integer.

        Video codecs like h264 require even dimensions, so we ensure
        composite dimensions are always even.
        """
        rounded = round(value)
        if rounded % 2 != 0:
            rounded += 1
        return float(rounded)

    def _compute_layout(self) -> None:
        """Compute scales and total dimensions for the composite."""
        n = len(self._scenes)

        if self._direction == "horizontal":
            # Scale each scene to match max height
            target_height = max(s.height for s in self._scenes)
            self._scales = [target_height / s.height for s in self._scenes]
            self._total_width = (
                sum(s.width * scale for s, scale in zip(self._scenes, self._scales))
                + self._gap * (n - 1)
            )
            self._total_height = target_height
        else:  # vertical
            # Scale each scene to match max width
            target_width = max(s.width for s in self._scenes)
            self._scales = [target_width / s.width for s in self._scenes]
            self._total_width = target_width
            self._total_height = (
                sum(s.height * scale for s, scale in zip(self._scenes, self._scales))
                + self._gap * (n - 1)
            )

        # Ensure dimensions are even for video codec compatibility
        self._total_width = self._round_to_even(self._total_width)
        self._total_height = self._round_to_even(self._total_height)

    @property
    def width(self) -> float:
        """Get the composite width."""
        return self._total_width

    @property
    def height(self) -> float:
        """Get the composite height."""
        return self._total_height

    @property
    def origin(self) -> Literal["center", "top-left"]:
        """Get the composite origin mode (from first scene or override)."""
        if self._origin_override is not None:
            return self._origin_override
        return self._scenes[0].origin  # type: ignore[return-value]

    @property
    def direction(self) -> Literal["horizontal", "vertical"]:
        """Get the stack direction."""
        return self._direction

    @property
    def gap(self) -> float:
        """Get the gap between scenes."""
        return self._gap

    @property
    def scenes(self) -> List[ComposableScene]:
        """Get the list of composed scenes."""
        return list(self._scenes)

    def to_drawing(
        self,
        frame_time: float = 0.0,
        render_scale: float = 1.0,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ) -> dw.Drawing:
        """Render the composite at a specific time point.

        Args:
            frame_time: Time point to render (0.0 to 1.0)
            render_scale: Scale factor for rendering
            width: Unused, for VSceneExporter compatibility
            height: Unused, for VSceneExporter compatibility

        Returns:
            A drawsvg Drawing

        Raises:
            ValueError: If frame_time is outside [0.0, 1.0]
        """
        _ = width, height  # Unused, for API compatibility

        if not 0.0 <= frame_time <= 1.0:
            raise ValueError(
                f"frame_time must be between 0.0 and 1.0, got {frame_time}"
            )

        # Apply render_scale to final dimensions
        final_width = self._total_width * render_scale
        final_height = self._total_height * render_scale

        drawing = dw.Drawing(final_width, final_height, origin=self.origin)

        # Determine starting offset based on origin mode
        if self.origin == "center":
            if self._direction == "horizontal":
                offset = -self._total_width / 2 * render_scale
            else:
                offset = -self._total_height / 2 * render_scale
        else:  # top-left
            offset = 0.0

        # Render each child scene with appropriate transforms
        for scene, scale in zip(self._scenes, self._scales):
            child_drawing = scene.to_drawing(frame_time=frame_time, render_scale=1.0)

            # Combined scale: child scale * render_scale
            total_scale = scale * render_scale

            # Build transform
            if self._direction == "horizontal":
                if self.origin == "center":
                    # For center origin: position child's center at correct location
                    child_center_x = offset + (scene.width * total_scale) / 2
                    transform = f"translate({child_center_x}, 0) scale({total_scale})"
                else:  # top-left
                    transform = f"translate({offset}, 0) scale({total_scale})"
                offset += scene.width * total_scale + self._gap * render_scale
            else:  # vertical
                if self.origin == "center":
                    # For center origin: position child's center at correct location
                    child_center_y = offset + (scene.height * total_scale) / 2
                    transform = f"translate(0, {child_center_y}) scale({total_scale})"
                else:  # top-left
                    transform = f"translate(0, {offset}) scale({total_scale})"
                offset += scene.height * total_scale + self._gap * render_scale

            # Create group with transform and add child elements
            group = dw.Group(transform=transform)
            for elem in child_drawing.elements:
                group.append(elem)
            drawing.append(group)

        return drawing

    def to_svg(
        self,
        frame_time: float = 0.0,
        render_scale: float = 1.0,
        width: Optional[float] = None,
        height: Optional[float] = None,
        filename: Optional[str] = None,
        log: bool = True,
    ) -> str:
        """Render the composite to SVG at a specific time point.

        Args:
            frame_time: Time point to render (0.0 to 1.0)
            render_scale: Scale factor for rendering
            width: Unused, for VSceneExporter compatibility
            height: Unused, for VSceneExporter compatibility
            filename: Optional filename to save SVG to
            log: Whether to log the save operation

        Returns:
            SVG string
        """
        _ = width, height  # Unused, for API compatibility
        drawing = self.to_drawing(frame_time=frame_time, render_scale=render_scale)
        svg_string: str = drawing.as_svg()  # type: ignore[assignment]

        if filename:
            drawing.save_svg(filename)
            if log:
                logger.info(f'SVG exported to "{filename}"')

        return svg_string

    def __repr__(self) -> str:
        return (
            f"VSceneComposite(scenes={len(self._scenes)}, "
            f"direction='{self._direction}', "
            f"size={self._total_width:.0f}x{self._total_height:.0f})"
        )
