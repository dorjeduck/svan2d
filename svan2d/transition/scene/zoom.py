"""Zoom transition - scale transform with opacity blend."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal

import drawsvg as dw

from svan2d.core.color import Color
from svan2d.transition.easing import linear

from .base import RenderContext, SceneTransition

if TYPE_CHECKING:
    from svan2d.vscene import VScene


ZoomDirection = Literal["in", "out"]


class Zoom(SceneTransition):
    """Zoom transition using scale transforms and opacity.

    The outgoing scene zooms and fades while the incoming scene
    zooms in from the opposite direction.

    Directions:
    - "in": Outgoing zooms in (grows), incoming zooms in from small
    - "out": Outgoing zooms out (shrinks), incoming zooms out from large

    Example:
        sequence = (
            VSceneSequence()
            .scene(scene1, duration=0.5)
            .transition(Zoom(direction="in", duration=0.3))
            .scene(scene2, duration=0.5)
        )
    """

    def __init__(
        self,
        direction: ZoomDirection = "in",
        duration: float = 0.5,
        easing: Callable[[float], float] = linear,
        max_scale: float = 2.0,
        overlapping: bool = False,
    ) -> None:
        """Initialize a zoom transition.

        Args:
            direction: Zoom direction ("in" or "out")
            duration: Duration of the transition
            easing: Easing function applied to zoom/opacity
            max_scale: Maximum scale factor at full zoom (default 2.0)
            overlapping: If True, scenes continue animating during transition
        """
        super().__init__(duration=duration, easing=easing, overlapping=overlapping)
        self.direction = direction
        self.max_scale = max_scale

    def composite(
        self,
        scene_out: "VScene",
        scene_in: "VScene",
        progress: float,
        time_out: float,
        time_in: float,
        ctx: RenderContext,
    ) -> dw.Drawing:
        """Composite scenes with zoom effect.

        Args:
            scene_out: The outgoing scene
            scene_in: The incoming scene
            progress: Progress through transition (0.0-1.0), already eased
            time_out: Current time within outgoing scene (0.0-1.0)
            time_in: Current time within incoming scene (0.0-1.0)
            ctx: Render context

        Returns:
            Drawing with zooming scenes
        """
        drawing = self._create_drawing(ctx)
        bg_x, bg_y, width, height = self._get_background_rect(ctx)

        # Draw solid background to prevent gray artifacts from opacity blending
        bg_color = self._get_interpolated_background(scene_out, scene_in, progress)
        if bg_color is not None:
            drawing.append(
                dw.Rectangle(bg_x, bg_y, width, height, fill=bg_color.to_rgb_string())
            )

        # Calculate zoom center based on origin
        if ctx.origin == "center":
            center_x, center_y = 0, 0
        else:
            center_x, center_y = width / 2, height / 2

        # Calculate scales and opacities
        out_scale, in_scale = self._calculate_scales(progress)
        opacity_out = 1.0 - progress
        opacity_in = progress

        # Render outgoing scene with zoom
        if opacity_out > 0:
            out_drawing = scene_out.to_drawing(
                frame_time=time_out,
                render_scale=ctx.render_scale,
            )
            out_transform = self._build_zoom_transform(center_x, center_y, out_scale)
            out_group = dw.Group(transform=out_transform, opacity=opacity_out)
            for child in out_drawing.elements:
                out_group.append(child)
            drawing.append(out_group)

        # Render incoming scene with zoom
        if opacity_in > 0:
            in_drawing = scene_in.to_drawing(
                frame_time=time_in,
                render_scale=ctx.render_scale,
            )
            in_transform = self._build_zoom_transform(center_x, center_y, in_scale)
            in_group = dw.Group(transform=in_transform, opacity=opacity_in)
            for child in in_drawing.elements:
                in_group.append(child)
            drawing.append(in_group)

        return drawing

    def _get_interpolated_background(
        self,
        scene_out: "VScene",
        scene_in: "VScene",
        progress: float,
    ) -> Color | None:
        """Get interpolated background color between two scenes.

        Args:
            scene_out: The outgoing scene
            scene_in: The incoming scene
            progress: Transition progress (0.0-1.0)

        Returns:
            Interpolated Color, or None if both scenes have no background
        """
        bg_out = getattr(scene_out, "background", None)
        bg_in = getattr(scene_in, "background", None)

        if bg_out is None and bg_in is None:
            return None
        if bg_out is None:
            return bg_in
        if bg_in is None:
            return bg_out

        # Interpolate between the two background colors
        return bg_out.interpolate(bg_in, progress)

    def _calculate_scales(self, progress: float) -> tuple[float, float]:
        """Calculate scale factors for both scenes.

        Args:
            progress: Transition progress (0.0-1.0)

        Returns:
            Tuple of (out_scale, in_scale)
        """
        if self.direction == "in":
            # Outgoing grows, incoming starts small and grows to normal
            out_scale = 1.0 + (self.max_scale - 1.0) * progress
            in_scale = (1.0 / self.max_scale) + (1.0 - 1.0 / self.max_scale) * progress
        else:  # out
            # Outgoing shrinks, incoming starts large and shrinks to normal
            out_scale = 1.0 - (1.0 - 1.0 / self.max_scale) * progress
            in_scale = self.max_scale - (self.max_scale - 1.0) * progress

        return out_scale, in_scale

    def _build_zoom_transform(
        self, center_x: float, center_y: float, scale: float
    ) -> str:
        """Build SVG transform string for zoom around center point.

        Args:
            center_x: X coordinate of zoom center
            center_y: Y coordinate of zoom center
            scale: Scale factor

        Returns:
            SVG transform string
        """
        # Scale around center: translate to center, scale, translate back
        return (
            f"translate({center_x},{center_y}) "
            f"scale({scale}) "
            f"translate({-center_x},{-center_y})"
        )

    def __repr__(self) -> str:
        return f"Zoom(direction='{self.direction}', duration={self.duration})"
