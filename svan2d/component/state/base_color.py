from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from svan2d.component.effect import Gradient, Pattern
from svan2d.component.state.base import State
from svan2d.transition import easing
from svan2d.core.color import Color
from svan2d.component.registry import get_renderer_class_for_state


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

    DEFAULT_EASING = {
        **State.DEFAULT_EASING,
        "fill_color": easing.linear,
        "fill_opacity": easing.linear,
        "fill_gradient": easing.linear,
        "fill_pattern": easing.linear,
        "stroke_color": easing.linear,
        "stroke_opacity": easing.linear,
        "stroke_width": easing.in_out,
        "stroke_gradient": easing.linear,
        "stroke_pattern": easing.linear,
    }

    # can be overridden by subclasses to add further angle attributes
    # used in interpolation (shortest angle distance)

    def __post_init__(self):
        super().__post_init__()
        self._normalize_color_field("fill_color")
        self._normalize_color_field("stroke_color")
