"""Slide transition - transform-based scene movement."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Literal

import drawsvg as dw

from svan2d.transition.easing import linear

from .base import RenderContext, SceneTransition

if TYPE_CHECKING:
    from svan2d.vscene import VScene


SlideDirection = Literal["left", "right", "up", "down"]


class Slide(SceneTransition):
    """Slide transition using transform translations.

    The outgoing scene slides out while the incoming scene slides in
    from the opposite direction.

    Directions specify where the outgoing scene moves to:
    - "left": Outgoing slides left, incoming slides from right
    - "right": Outgoing slides right, incoming slides from left
    - "up": Outgoing slides up, incoming slides from bottom
    - "down": Outgoing slides down, incoming slides from top

    Example:
        sequence = (
            VSceneSequence()
            .scene(scene1, duration=0.5)
            .transition(Slide(direction="left", duration=0.2))
            .scene(scene2, duration=0.5)
        )
    """

    def __init__(
        self,
        direction: SlideDirection = "left",
        duration: float = 0.5,
        easing: Callable[[float], float] = linear,
        overlapping: bool = False,
    ) -> None:
        """Initialize a slide transition.

        Args:
            direction: Direction the outgoing scene moves
            duration: Duration of the transition
            easing: Easing function applied to the slide movement
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
        """Composite scenes with sliding movement.

        Args:
            scene_out: The outgoing scene
            scene_in: The incoming scene
            progress: Progress through transition (0.0-1.0), already eased
            time_out: Current time within outgoing scene (0.0-1.0)
            time_in: Current time within incoming scene (0.0-1.0)
            ctx: Render context

        Returns:
            Drawing with sliding scenes
        """
        drawing = self._create_drawing(ctx)
        _, _, width, height = self._get_background_rect(ctx)

        # Calculate offsets based on direction
        out_offset, in_offset = self._calculate_offsets(progress, width, height)

        # Render outgoing scene with offset
        out_drawing = scene_out.to_drawing(
            frame_time=time_out,
            render_scale=ctx.render_scale,
        )
        out_transform = f"translate({out_offset[0]},{out_offset[1]})"
        out_group = dw.Group(transform=out_transform)
        for child in out_drawing.elements:
            out_group.append(child)
        drawing.append(out_group)

        # Render incoming scene with offset
        in_drawing = scene_in.to_drawing(
            frame_time=time_in,
            render_scale=ctx.render_scale,
        )
        in_transform = f"translate({in_offset[0]},{in_offset[1]})"
        in_group = dw.Group(transform=in_transform)
        for child in in_drawing.elements:
            in_group.append(child)
        drawing.append(in_group)

        return drawing

    def _calculate_offsets(
        self,
        progress: float,
        width: float,
        height: float,
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        """Calculate translation offsets for both scenes.

        Args:
            progress: Transition progress (0.0-1.0)
            width: Scene width
            height: Scene height

        Returns:
            Tuple of (out_offset, in_offset), each as (x, y)
        """
        if self.direction == "left":
            # Outgoing slides left, incoming from right
            out_offset = (-width * progress, 0)
            in_offset = (width * (1 - progress), 0)

        elif self.direction == "right":
            # Outgoing slides right, incoming from left
            out_offset = (width * progress, 0)
            in_offset = (-width * (1 - progress), 0)

        elif self.direction == "up":
            # Outgoing slides up, incoming from bottom
            out_offset = (0, -height * progress)
            in_offset = (0, height * (1 - progress))

        else:  # down
            # Outgoing slides down, incoming from top
            out_offset = (0, height * progress)
            in_offset = (0, -height * (1 - progress))

        return out_offset, in_offset

    def __repr__(self) -> str:
        return f"Slide(direction='{self.direction}', duration={self.duration})"
