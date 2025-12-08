from dataclasses import dataclass
from .base import State
from svan2d.component.registry import renderer
from svan2d.component.renderer.raw_svg import RawSvgRenderer


@renderer(RawSvgRenderer)
@dataclass(frozen=True)
class RawSvgState(State):
    """
    State for raw SVG data rendering.
    """

    svg_data: str = ""

