"""Abstract base class for renderers with multiple path variants and text labels"""

from __future__ import annotations

from dataclasses import dataclass
from svan2d.primitive.registry import renderer
from svan2d.primitive.renderer.path_and_text_variants import PathAndTextVariantsRenderer
from svan2d.primitive.state.base_color import ColorState
from svan2d.core.color import Color


@renderer(PathAndTextVariantsRenderer)
@dataclass(frozen=True)
class PathAndTextVariantsState(ColorState):
    """Base state class for multi-path renderers with text labels"""

    size: float = 500
    # Which of the renderer's PATH_VARIANTS to draw; None takes the first one.
    variant: str | None = None

    # Text attributes
    # The label to draw; None takes the variant's own text.
    text: str | None = None
    font_size: float = 35
    letter_spacing: float = 0
    font_family: str = "Comfortaa"
    text_align: str = "left"
    font_weight: str = "normal"
    text_color: Color | None = Color.NONE

    def __post_init__(self):
        super().__post_init__()
        self._none_color("fill_color")
        self._none_color("stroke_color")
        self._none_color("text_color")
