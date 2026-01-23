"""Text renderer implementation for new architecture"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union

from svan2d.component.registry import renderer
from svan2d.component.renderer.text import TextRenderer
from svan2d.component.state.base_color import ColorState
from svan2d.core.color import Color


@renderer(TextRenderer)
@dataclass(frozen=True)
class TextState(ColorState):
    """State class for text elements"""

    font_size: float = 16

    letter_spacing: float = 0  # Additional spacing between letters

    text: Union[str, List[str]] = ""
    font_family: str = "Arial"
    text_align: str = "middle"
    font_weight: str = "normal"
    text_anchor: str = "middle"
    dominant_baseline: str = "central"

    def __post_init__(self):
        super().__post_init__()
        self._none_color("fill_color")
