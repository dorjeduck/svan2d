"""Text renderer implementation for new architecture"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from svan2d.core.em import Em, letter_spacing_px
from svan2d.primitive.registry import renderer, skia_renderer
from svan2d.primitive.renderer.text import TextRenderer
from svan2d.primitive.state.base_color import ColorState


class TextRendering(Enum):
    """SVG text-rendering attribute options."""

    AUTO = "auto"
    OPTIMIZE_SPEED = "optimizeSpeed"
    OPTIMIZE_LEGIBILITY = "optimizeLegibility"
    GEOMETRIC_PRECISION = "geometricPrecision"


@skia_renderer("svan2d.primitive.renderer.skia.text:TextSkiaRenderer")
@renderer(TextRenderer)
@dataclass(frozen=True)
class TextState(ColorState):
    """State class for text elements"""

    font_size: float = 16

    # Additional spacing after every letter: pixels, or em as in SVG, given as
    # Em(0.04) or "0.04em", a share of the font size that follows it
    letter_spacing: float | Em | str = 0

    text: str | list[str] = ""
    font_family: str = "Arial"
    font_weight: str = "normal"
    text_anchor: str = "middle"
    dominant_baseline: str = "central"
    text_rendering: TextRendering = TextRendering.AUTO

    def __post_init__(self):
        super().__post_init__()
        self._none_color("fill_color")
        if isinstance(self.letter_spacing, str):
            self._set_field("letter_spacing", Em.parse(self.letter_spacing))

    @property
    def letter_spacing_px(self) -> float:
        """The spacing in pixels at this state's font size."""
        return letter_spacing_px(self.letter_spacing, self.font_size)

    def interpolate_field(
        self, end: Any, field_name: str, start_value: Any, end_value: Any, t: float
    ) -> Any:
        """Letter spacing in em blends in em, so it keeps following the font
        size; between pixels and em it blends in pixels."""
        if field_name != "letter_spacing":
            return NotImplemented
        if isinstance(start_value, Em) and isinstance(end_value, Em):
            return Em(start_value.value + (end_value.value - start_value.value) * t)
        if isinstance(start_value, Em) or isinstance(end_value, Em):
            start_px = letter_spacing_px(start_value, self.font_size)
            end_px = letter_spacing_px(end_value, end.font_size)
            return start_px + (end_px - start_px) * t
        return NotImplemented