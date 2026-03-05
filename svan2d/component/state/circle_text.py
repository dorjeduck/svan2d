from __future__ import annotations

from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.circle_text import CircleTextRenderer

from .text import TextState


@renderer(CircleTextRenderer)
@dataclass(frozen=True)
class CircleTextState(TextState):
    """State for text laid out along a circular path."""

    radius: float = 100  # Radius of the circle path
    rotation: float = 0
    angles: list[float] | None = None

    text: str | list[str] = ""
    text_facing_inward: bool = True
    font_family: str = "Arial"
    text_align: str = "middle"
    font_weight: str = "normal"
    text_anchor: str = "middle"
    dominant_baseline: str = "central"
