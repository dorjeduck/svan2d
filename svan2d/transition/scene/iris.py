"""Iris transition - circular clip path reveal."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable, Literal
from uuid import uuid4

import drawsvg as dw

from svan2d.transition.easing import linear

from .base import RenderContext, SceneTransition

if TYPE_CHECKING:
    from svan2d.vscene import VScene


IrisDirection = Literal["open", "close"]


class Iris(SceneTransition):
    """Iris transition using circular clip paths.

    Creates a circular reveal/hide effect, similar to the classic
    film iris wipe.

    Directions:
    - "open": Circle expands from center to reveal incoming scene
    - "close": Circle shrinks to hide outgoing scene

    Example:
        sequence = (
            VSceneSequence()
            .scene(scene1, duration=0.5)
            .transition(Iris(direction="open", duration=0.3))
            .scene(scene2, duration=0.5)
        )
    """

    def __init__(
        self,
        direction: IrisDirection = "open",
        duration: float = 0.5,
        easing: Callable[[float], float] = linear,
        center: tuple[float, float] | None = None,
        overlapping: bool = False,
    ) -> None:
        """Initialize an iris transition.

        Args:
            direction: "open" (expand) or "close" (shrink)
            duration: Duration of the transition
            easing: Easing function applied to the circle radius
            center: Optional (x, y) center point in scene coordinates.
                   If None, uses scene center (0,0 for center origin).
            overlapping: If True, scenes continue animating during transition
        """
        super().__init__(duration=duration, easing=easing, overlapping=overlapping)
        self.direction = direction
        self.center = center

    def composite(
        self,
        scene_out: "VScene",
        scene_in: "VScene",
        progress: float,
        time_out: float,
        time_in: float,
        ctx: RenderContext,
    ) -> dw.Drawing:
        """Composite scenes with iris circle effect.

        Args:
            scene_out: The outgoing scene
            scene_in: The incoming scene
            progress: Progress through transition (0.0-1.0), already eased
            time_out: Current time within outgoing scene (0.0-1.0)
            time_in: Current time within incoming scene (0.0-1.0)
            ctx: Render context

        Returns:
            Drawing with iris effect
        """
        drawing = self._create_drawing(ctx)
        _, _, width, height = self._get_background_rect(ctx)

        # Calculate center point
        if self.center is not None:
            center_x, center_y = self.center
        elif ctx.origin == "center":
            center_x, center_y = 0, 0
        else:
            center_x, center_y = width / 2, height / 2

        # Max radius to cover entire scene from center
        max_radius = math.sqrt(
            (width / 2 + abs(center_x)) ** 2 + (height / 2 + abs(center_y)) ** 2
        )

        # Generate unique ID for clip path
        clip_id = f"iris-{uuid4().hex[:8]}"

        # Calculate current radius based on direction and progress
        if self.direction == "open":
            # Circle expands to reveal incoming scene
            radius = max_radius * progress
            # Draw outgoing scene as background
            out_drawing = scene_out.to_drawing(
                frame_time=time_out,
                render_scale=ctx.render_scale,
            )
            for child in out_drawing.elements:
                drawing.append(child)

            # Draw incoming scene clipped by expanding circle
            clip = dw.ClipPath(id=clip_id)
            clip.append(dw.Circle(center_x, center_y, radius))
            drawing.append_def(clip)

            in_drawing = scene_in.to_drawing(
                frame_time=time_in,
                render_scale=ctx.render_scale,
            )
            in_group = dw.Group(clip_path=f"url(#{clip_id})")
            for child in in_drawing.elements:
                in_group.append(child)
            drawing.append(in_group)

        else:  # close
            # Circle shrinks to hide outgoing scene
            radius = max_radius * (1 - progress)
            # Draw incoming scene as background
            in_drawing = scene_in.to_drawing(
                frame_time=time_in,
                render_scale=ctx.render_scale,
            )
            for child in in_drawing.elements:
                drawing.append(child)

            # Draw outgoing scene clipped by shrinking circle
            clip = dw.ClipPath(id=clip_id)
            clip.append(dw.Circle(center_x, center_y, radius))
            drawing.append_def(clip)

            out_drawing = scene_out.to_drawing(
                frame_time=time_out,
                render_scale=ctx.render_scale,
            )
            out_group = dw.Group(clip_path=f"url(#{clip_id})")
            for child in out_drawing.elements:
                out_group.append(child)
            drawing.append(out_group)

        return drawing

    def __repr__(self) -> str:
        return f"Iris(direction='{self.direction}', duration={self.duration})"
