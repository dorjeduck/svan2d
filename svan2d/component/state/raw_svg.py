from dataclasses import dataclass

from svan2d.component.registry import renderer
from svan2d.component.renderer.raw_svg import RawSvgRenderer

from .base import State


@renderer(RawSvgRenderer)
@dataclass(frozen=True)
class RawSvgState(State):
    """
    State for raw SVG data rendering.
    """

    svg_data: str = ""

