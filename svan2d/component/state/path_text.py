# ============================================================================
# svan2d/components/path_text.py
# ============================================================================
"""PathText component - Text that follows any SVG path with morphing support"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union

from svan2d.component.registry import renderer
from svan2d.component.renderer.path_text import PathTextRenderer
from svan2d.path import SVGPath

from .text import TextState


@renderer(PathTextRenderer)
@dataclass(frozen=True)
class PathTextState(TextState):
    """State class for text elements following an SVG path

    Supports text morphing by animating the path field.
    """

    data: Union[str, SVGPath] = "M 0,0 L 10,10 L 0,20 Z"  # Default straight line path
    offset: float = 0.5  # Position along path (0.0 to 1.0)
    offsets: Optional[List[float]] = None  # For multiple texts

    text: Union[str, List[str]] = "Text"

    # Path rendering options
    flip_text: bool = False  # Flip text upside down (for bottom of curves)

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.data, str):
            self._set_field("data", SVGPath.from_string(self.data))
