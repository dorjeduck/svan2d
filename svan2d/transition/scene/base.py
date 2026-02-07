"""Base classes for scene transitions.

Scene transitions composite two scenes during overlap periods,
enabling effects like fades, wipes, slides, etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

import drawsvg as dw

from svan2d.core.enums import Origin
from svan2d.transition.easing import linear

if TYPE_CHECKING:
    from svan2d.vscene import VScene


@dataclass(frozen=True)
class RenderContext:
    """Context passed to transition composite methods.

    Contains scene dimensions and rendering parameters.

    Attributes:
        width: Scene width in pixels
        height: Scene height in pixels
        render_scale: Scale factor for rendering (default 1.0)
        origin: Coordinate origin mode ("center" or "top-left")
    """

    width: float
    height: float
    render_scale: float = 1.0
    origin: Origin = Origin.CENTER


class SceneTransition(ABC):
    """Abstract base class for scene transitions.

    A scene transition composites two scenes during an overlap period,
    creating visual effects like fades, wipes, slides, etc.

    Subclasses must implement the `composite` method which receives:
    - The outgoing scene (scene_out) and its current time
    - The incoming scene (scene_in) and its current time
    - A progress value (0.0-1.0) within the transition
    - A render context with dimensions and settings

    Attributes:
        duration: Duration of the transition as fraction of total sequence time
        easing: Easing function applied to the progress value
        overlapping: If True, scenes continue animating during the transition
    """

    def __init__(
        self,
        duration: float = 0.5,
        easing: Callable[[float], float] = linear,
        overlapping: bool = False,
    ) -> None:
        """Initialize a scene transition.

        Args:
            duration: Duration of the transition (0.0-1.0 of total sequence time)
            easing: Easing function to apply to progress (default: linear)
            overlapping: If True, scenes continue animating during the transition.
                        If False (default), transition blends scene_out at t=1.0
                        with scene_in at t=0.0.

        Raises:
            ValueError: If duration is not positive
        """
        if duration <= 0:
            raise ValueError(f"duration must be positive, got {duration}")
        self.duration = duration
        self.easing = easing
        self.overlapping = overlapping

    @abstractmethod
    def composite(
        self,
        scene_out: "VScene",
        scene_in: "VScene",
        progress: float,
        time_out: float,
        time_in: float,
        ctx: RenderContext,
    ) -> dw.Drawing:
        """Composite two scenes during a transition.

        This method is called for each frame during a transition, receiving
        both scenes and their respective time points. The progress value
        (0.0-1.0) indicates how far through the transition we are.

        Args:
            scene_out: The outgoing scene (transitioning away)
            scene_in: The incoming scene (transitioning in)
            progress: Progress through the transition (0.0-1.0), already eased
            time_out: Current time within the outgoing scene (0.0-1.0)
            time_in: Current time within the incoming scene (0.0-1.0)
            ctx: Render context with dimensions and settings

        Returns:
            A drawsvg Drawing containing the composited result
        """
        pass

    def _create_drawing(self, ctx: RenderContext) -> dw.Drawing:
        """Create a new drawing with the appropriate dimensions and origin.

        Args:
            ctx: Render context with dimensions and settings

        Returns:
            A new drawsvg Drawing
        """
        width = ctx.width * ctx.render_scale
        height = ctx.height * ctx.render_scale
        return dw.Drawing(width, height, origin=ctx.origin)

    def _get_background_rect(
        self, ctx: RenderContext
    ) -> tuple[float, float, float, float]:
        """Get background rectangle coordinates based on origin mode.

        Args:
            ctx: Render context with dimensions and settings

        Returns:
            Tuple of (x, y, width, height) for background rectangle
        """
        width = ctx.width * ctx.render_scale
        height = ctx.height * ctx.render_scale

        if ctx.origin == "center":
            return (-width / 2, -height / 2, width, height)
        else:  # top-left
            return (0, 0, width, height)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(duration={self.duration})"
