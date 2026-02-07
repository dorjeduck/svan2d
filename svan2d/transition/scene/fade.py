"""Fade transition - opacity-based crossfade between scenes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import drawsvg as dw

from svan2d.core.color import Color
from svan2d.transition.easing import linear

from .base import RenderContext, SceneTransition

if TYPE_CHECKING:
    from svan2d.vscene import VScene


class Fade(SceneTransition):
    """Crossfade transition using opacity blending.

    The outgoing scene fades out while the incoming scene fades in,
    creating a smooth dissolve effect.

    Example:
        sequence = (
            VSceneSequence()
            .scene(scene1, duration=0.5)
            .transition(Fade(duration=0.2, easing=easing.in_out))
            .scene(scene2, duration=0.5)
        )
    """

    def __init__(
        self,
        duration: float = 0.5,
        easing: Callable[[float], float] = linear,
        overlapping: bool = False,
    ) -> None:
        """Initialize a fade transition.

        Args:
            duration: Duration of the transition (0.0-1.0 of total sequence time)
            easing: Easing function applied to the opacity interpolation
            overlapping: If True, scenes continue animating during transition
        """
        super().__init__(duration=duration, easing=easing, overlapping=overlapping)

    def composite(
        self,
        scene_out: "VScene",
        scene_in: "VScene",
        progress: float,
        time_out: float,
        time_in: float,
        ctx: RenderContext,
    ) -> dw.Drawing:
        """Composite scenes with opacity crossfade.

        Args:
            scene_out: The outgoing scene
            scene_in: The incoming scene
            progress: Progress through transition (0.0-1.0), already eased
            time_out: Current time within outgoing scene (0.0-1.0)
            time_in: Current time within incoming scene (0.0-1.0)
            ctx: Render context

        Returns:
            Drawing with crossfaded scenes
        """
        drawing = self._create_drawing(ctx)
        bg_x, bg_y, width, height = self._get_background_rect(ctx)

        # Draw solid background to prevent gray artifacts from opacity blending
        bg_color = self._get_interpolated_background(scene_out, scene_in, progress)
        if bg_color is not None:
            drawing.append(
                dw.Rectangle(bg_x, bg_y, width, height, fill=bg_color.to_rgb_string())
            )

        # Calculate opacities - linear crossfade
        opacity_out = 1.0 - progress
        opacity_in = progress

        # Render outgoing scene with fade-out opacity
        if opacity_out > 0:
            out_drawing = scene_out.to_drawing(
                frame_time=time_out,
                render_scale=ctx.render_scale,
            )
            out_group = dw.Group(opacity=opacity_out)
            for child in out_drawing.elements:
                out_group.append(child)
            drawing.append(out_group)

        # Render incoming scene with fade-in opacity
        if opacity_in > 0:
            in_drawing = scene_in.to_drawing(
                frame_time=time_in,
                render_scale=ctx.render_scale,
            )
            in_group = dw.Group(opacity=opacity_in)
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
