"""Wipe transition - directional reveal using clip paths."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal
from uuid import uuid4

import drawsvg as dw

from svan2d.core.color import Color
from svan2d.transition.easing import linear

from .base import RenderContext, SceneTransition

if TYPE_CHECKING:
    from svan2d.vscene import VScene


WipeDirection = Literal["left", "right", "up", "down"]


class Wipe(SceneTransition):
    """Wipe transition using directional clip paths.

    The incoming scene is revealed from one direction while
    the outgoing scene is hidden in the same direction.

    Directions:
    - "left": Reveal from right to left
    - "right": Reveal from left to right
    - "up": Reveal from bottom to top
    - "down": Reveal from top to bottom

    Example:
        sequence = (
            VSceneSequence()
            .scene(scene1, duration=0.5)
            .transition(Wipe(direction="left", duration=0.2))
            .scene(scene2, duration=0.5)
        )
    """

    def __init__(
        self,
        direction: WipeDirection = "left",
        duration: float = 0.5,
        easing: Callable[[float], float] = linear,
        overlapping: bool = False,
    ) -> None:
        """Initialize a wipe transition.

        Args:
            direction: Direction of the wipe ("left", "right", "up", "down")
            duration: Duration of the transition
            easing: Easing function applied to the wipe progress
            overlapping: If True, scenes continue animating during transition
        """
        super().__init__(duration=duration, easing=easing, overlapping=overlapping)
        self.direction = direction

    def composite(
        self,
        scene_out: "VScene",
        scene_in: "VScene",
        progress: float,
        time_out: float,
        time_in: float,
        ctx: RenderContext,
    ) -> dw.Drawing:
        """Composite scenes with directional wipe.

        Args:
            scene_out: The outgoing scene
            scene_in: The incoming scene
            progress: Progress through transition (0.0-1.0), already eased
            time_out: Current time within outgoing scene (0.0-1.0)
            time_in: Current time within incoming scene (0.0-1.0)
            ctx: Render context

        Returns:
            Drawing with wiped scenes
        """
        drawing = self._create_drawing(ctx)
        bg_x, bg_y, width, height = self._get_background_rect(ctx)

        # Draw solid background to prevent seam artifacts at clip boundary
        bg_color = self._get_background_color(scene_out, scene_in)
        if bg_color is not None:
            drawing.append(
                dw.Rectangle(bg_x, bg_y, width, height, fill=bg_color.to_rgb_string())
            )

        # Generate unique IDs for clip paths
        clip_out_id = f"wipe-out-{uuid4().hex[:8]}"
        clip_in_id = f"wipe-in-{uuid4().hex[:8]}"

        # Calculate clip rectangles based on direction
        out_rect, in_rect = self._calculate_clip_rects(
            progress, bg_x, bg_y, width, height
        )

        # Create clip paths
        clip_out = dw.ClipPath(id=clip_out_id)
        clip_out.append(dw.Rectangle(*out_rect))
        drawing.append_def(clip_out)

        clip_in = dw.ClipPath(id=clip_in_id)
        clip_in.append(dw.Rectangle(*in_rect))
        drawing.append_def(clip_in)

        # Render outgoing scene with clip
        out_drawing = scene_out.to_drawing(
            frame_time=time_out,
            render_scale=ctx.render_scale,
        )
        out_group = dw.Group(clip_path=f"url(#{clip_out_id})")
        for child in out_drawing.elements:
            out_group.append(child)
        drawing.append(out_group)

        # Render incoming scene with clip
        in_drawing = scene_in.to_drawing(
            frame_time=time_in,
            render_scale=ctx.render_scale,
        )
        in_group = dw.Group(clip_path=f"url(#{clip_in_id})")
        for child in in_drawing.elements:
            in_group.append(child)
        drawing.append(in_group)

        return drawing

    def _calculate_clip_rects(
        self,
        progress: float,
        bg_x: float,
        bg_y: float,
        width: float,
        height: float,
    ) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
        """Calculate clip rectangles for outgoing and incoming scenes.

        Args:
            progress: Transition progress (0.0-1.0)
            bg_x: Background x position
            bg_y: Background y position
            width: Scene width
            height: Scene height

        Returns:
            Tuple of (out_rect, in_rect), each as (x, y, w, h)
        """
        if self.direction == "left":
            # Wipe from right to left
            out_w = width * (1 - progress)
            in_x = bg_x + out_w
            in_w = width * progress
            out_rect = (bg_x, bg_y, out_w, height)
            in_rect = (in_x, bg_y, in_w, height)

        elif self.direction == "right":
            # Wipe from left to right
            in_w = width * progress
            out_x = bg_x + in_w
            out_w = width * (1 - progress)
            out_rect = (out_x, bg_y, out_w, height)
            in_rect = (bg_x, bg_y, in_w, height)

        elif self.direction == "up":
            # Wipe from bottom to top
            out_h = height * (1 - progress)
            in_y = bg_y + out_h
            in_h = height * progress
            out_rect = (bg_x, bg_y, width, out_h)
            in_rect = (bg_x, in_y, width, in_h)

        else:  # down
            # Wipe from top to bottom
            in_h = height * progress
            out_y = bg_y + in_h
            out_h = height * (1 - progress)
            out_rect = (bg_x, out_y, width, out_h)
            in_rect = (bg_x, bg_y, width, in_h)

        return out_rect, in_rect

    @staticmethod
    def _get_background_color(
        scene_out: "VScene",
        scene_in: "VScene",
    ) -> Color | None:
        """Get a background color from the scenes for the composite drawing.

        Uses the outgoing scene's background, falling back to incoming.
        """
        bg = getattr(scene_out, "background", None)
        if bg is not None:
            return bg
        return getattr(scene_in, "background", None)

    def __repr__(self) -> str:
        return f"Wipe(direction='{self.direction}', duration={self.duration})"
