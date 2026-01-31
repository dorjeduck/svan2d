"""Text path state - text rendered as SVG paths for smooth animation."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import List, Union

from svan2d.component.registry import renderer
from svan2d.component.renderer.text_path import TextPathRenderer
from svan2d.component.state.base_color import ColorState


@lru_cache(maxsize=16)
def _load_font_cached(font_path: str):
    """Load and cache font files."""
    from svan2d.font.glyph_extractor import load_font

    return load_font(font_path)


@renderer(TextPathRenderer)
@dataclass(frozen=True)
class TextPathState(ColorState):
    """State for text rendered as SVG paths.

    Similar to TextState but renders text as <path> elements instead of <text>.
    This eliminates font hinting artifacts during animation/transformation,
    giving smooth scaling and rotation.

    Requires a font file path (TTF or OTF) instead of a font family name.

    Example:
        # For animated/transformed text - smooth scaling
        state = TextPathState(
            text="Hello",
            font_path="/path/to/Arial.ttf",
            font_size=24,
            fill_color=Color("#000000"),
        )

        # Compare with TextState for static text:
        # state = TextState(text="Hello", font_family="Arial", font_size=24)
    """

    text: Union[str, List[str]] = ""
    font_path: str = ""
    font_size: float = 16

    text_anchor: str = "middle"  # start, middle, end
    dominant_baseline: str = "central"  # auto, central, middle, hanging, etc.

    def __post_init__(self):
        super().__post_init__()
        self._none_color("fill_color")

        if not self.font_path:
            raise ValueError("font_path is required for TextPathState")

    def _get_font(self):
        """Get the cached font object."""
        return _load_font_cached(self.font_path)
