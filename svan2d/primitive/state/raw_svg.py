from dataclasses import dataclass

from svan2d.primitive.registry import renderer, skia_renderer
from svan2d.primitive.renderer.raw_svg import RawSvgRenderer

from .base import State


@skia_renderer("svan2d.primitive.renderer.skia.raw_svg:RawSvgSkiaRenderer")
@renderer(RawSvgRenderer)
@dataclass(frozen=True)
class RawSvgState(State):
    """
    State for raw SVG data rendering.
    """

    svg_data: str = ""

