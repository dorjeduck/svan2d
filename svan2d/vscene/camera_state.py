"""Camera state for animated scene-level transforms."""

from dataclasses import dataclass
from typing import Optional

from svan2d.component.state.base import State
from svan2d.core.point2d import Point2D


@dataclass(frozen=True)
class CameraState(State):
    """State for animated scene-level camera transforms.

    Enables animated zoom, pan, and rotation at the scene level.

    Inherits from State:
        pos: Pan offset (Point2D)
        scale: Zoom factor (1.0 = normal, <1 = zoom out, >1 = zoom in)
        rotation: Rotation in degrees

    Additional attributes:
        pivot: Zoom/rotation center point (Point2D)
    """

    pivot: Point2D | None = None

    def __post_init__(self):
        super().__post_init__()
        if self.pivot is None:
            self._set_field("pivot", Point2D(0, 0))
