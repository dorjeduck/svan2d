from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from svan2d.component.effect import Gradient, Pattern
from svan2d.component.state.base import State
from svan2d.core.color import Color


@dataclass(frozen=True)
class ColorState(State):
    """Abstract base class for all state classes

    Contains common visual attributes that all renderers can use.
    Subclasses add renderer-specific attributes.

    Default values for x, y, scale, opacity, and rotation are read from
    the configuration system if not explicitly provided.
    """

    fill_color: Optional[Color] = Color.NONE
    fill_opacity: float = 1
    fill_gradient: Optional[Gradient] = None
    fill_pattern: Optional[Pattern] = None
    stroke_color: Optional[Color] = Color.NONE
    stroke_opacity: float = 1
    stroke_width: float = 1
    stroke_gradient: Optional[Gradient] = None
    stroke_pattern: Optional[Pattern] = None
    non_scaling_stroke: bool = False

    def __post_init__(self):
        super().__post_init__()
        self._normalize_color_field("fill_color")
        self._normalize_color_field("stroke_color")
