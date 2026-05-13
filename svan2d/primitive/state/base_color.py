from __future__ import annotations

from dataclasses import dataclass

from svan2d.primitive.effect import Gradient, Pattern
from svan2d.primitive.state.base import State
from svan2d.core.color import Color


@dataclass(frozen=True)
class ColorState(State):
    """Base class adding fill/stroke color, opacity, and gradient/pattern support to State."""

    fill_color: Color | None = Color.NONE
    fill_opacity: float = 1
    fill_gradient: Gradient | None = None
    fill_pattern: Pattern | None = None
    stroke_color: Color | None = Color.NONE
    stroke_opacity: float = 1
    stroke_width: float = 1
    stroke_gradient: Gradient | None = None
    stroke_pattern: Pattern | None = None
    non_scaling_stroke: bool = False

    def __post_init__(self):
        super().__post_init__()
        self._normalize_color_field("fill_color")
        self._normalize_color_field("stroke_color")
