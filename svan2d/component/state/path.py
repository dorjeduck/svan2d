from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Union

from svan2d.component.registry import renderer
from svan2d.component.renderer.path import PathRenderer
from svan2d.component.state.base_color import ColorState
from svan2d.core.color import Color
from svan2d.path.svg_path import SVGPath


class MorphMethod(StrEnum):
    """
    Path morphing method selection.

    Members:
        STROKE: Use native engine for open paths or strokes.
        SHAPE: Use Flubber algorithm for closed shapes or fills.
        AUTO: Automatically detect method based on path structure.
    """

    STROKE = "stroke"
    SHAPE = "shape"
    AUTO = "auto"


class StrokeLinecap(StrEnum):
    """
    SVG stroke-linecap values.

    Members:
        BUTT: The stroke ends exactly at the path endpoint (no extension).
        ROUND: The stroke ends with a semicircular cap extending beyond the endpoint.
        SQUARE: The stroke ends with a square cap extending beyond the endpoint.
    """

    BUTT = "butt"
    ROUND = "round"
    SQUARE = "square"


class StrokeLinejoin(StrEnum):
    """
    SVG stroke-linejoin values.

    Members:
        MITER: Sharp corner extending to the intersection of path segments.
        ROUND: Rounded corner at the join of path segments.
        BEVEL: Flattened corner, creating a straight line between path segment ends.
    """

    MITER = "miter"
    ROUND = "round"
    BEVEL = "bevel"


class FillRule(StrEnum):
    """
    SVG fill-rule values, defining how shapes are filled.

    Members:
        NONZERO: Fills areas based on the non-zero winding rule.
        EVENODD: Fills areas based on the even-odd rule.
    """

    NONZERO = "nonzero"
    EVENODD = "evenodd"


@renderer(PathRenderer)
@dataclass(frozen=True)
class PathState(ColorState):
    """State for SVG path rendering and morphing"""

    data: Union[str, SVGPath] = "M 0,0 L 10,10 L 0,20 Z"  # Default path data

    # Stroke attributes

    stroke_linecap: Union[StrokeLinecap, str] = StrokeLinecap.BUTT
    stroke_linejoin: Union[StrokeLinejoin, str] = StrokeLinejoin.MITER
    stroke_dasharray: str | None = None

    # Fill attributes
    fill_rule: Union[str, FillRule] = FillRule.EVENODD  # nonzero, evenodd

    # General attributes
    opacity: float = 1.0

    # Morphing method
    morph_method: Optional[Union[MorphMethod, str]] = None

    def __post_init__(self):
        super().__post_init__()

        if isinstance(self.data, str):
            self._set_field("data", SVGPath.from_string(self.data))

        self._none_color("fill_color")
        self._none_color("stroke_color")
