"""Abstract base class for renderers with multiple path variants"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from svan2d.component.registry import renderer
from svan2d.component.renderer.path_variants import PathVariantsRenderer
from svan2d.component.state.base_color import ColorState
from svan2d.core.color import Color


@renderer(PathVariantsRenderer)
@dataclass(frozen=True)
class PathVariantsState(ColorState):
    """Base state class for multi-path renderers"""

    size: float = 50
    case_sensitive: bool = False

    def __post_init__(self):
        super().__post_init__()
        self._none_color("fill_color")
        self._none_color("stroke_color")
