"""Per-primitive Skia renderers (one module per primitive).

Importing this package imports every renderer module, which runs the
@skia_renderer decorators and populates the Skia registry. Mirrors the SVG
renderer files in svan2d/primitive/renderer/, but draws directly to a
skia.Canvas (see svan2d.skia).
"""

from svan2d.primitive.renderer.skia.arc import ArcSkiaRenderer
from svan2d.primitive.renderer.skia.astroid import AstroidSkiaRenderer
from svan2d.primitive.renderer.skia.base_vertex import VertexSkiaRenderer
from svan2d.primitive.renderer.skia.circle import CircleSkiaRenderer
from svan2d.primitive.renderer.skia.circle_text import CircleTextSkiaRenderer
from svan2d.primitive.renderer.skia.ellipse import EllipseSkiaRenderer
from svan2d.primitive.renderer.skia.image import ImageSkiaRenderer
from svan2d.primitive.renderer.skia.line import LineSkiaRenderer
from svan2d.primitive.renderer.skia.number import NumberSkiaRenderer
from svan2d.primitive.renderer.skia.path import PathSkiaRenderer
from svan2d.primitive.renderer.skia.path_and_text_variants import (
    PathAndTextVariantsSkiaRenderer,
)
from svan2d.primitive.renderer.skia.path_band import PathBandSkiaRenderer
from svan2d.primitive.renderer.skia.path_text import PathTextSkiaRenderer
from svan2d.primitive.renderer.skia.path_variants import PathVariantsSkiaRenderer
from svan2d.primitive.renderer.skia.polygon import PolygonSkiaRenderer
from svan2d.primitive.renderer.skia.radial_segments import RadialSegmentsSkiaRenderer
from svan2d.primitive.renderer.skia.raw_svg import RawSvgSkiaRenderer
from svan2d.primitive.renderer.skia.rectangle import RectangleSkiaRenderer
from svan2d.primitive.renderer.skia.ring import RingSkiaRenderer
from svan2d.primitive.renderer.skia.square import SquareSkiaRenderer
from svan2d.primitive.renderer.skia.star import StarSkiaRenderer
from svan2d.primitive.renderer.skia.state_collection import (
    StateCollectionSkiaRenderer,
)
from svan2d.primitive.renderer.skia.text import TextSkiaRenderer
from svan2d.primitive.renderer.skia.text_path import TextPathSkiaRenderer
from svan2d.primitive.renderer.skia.triangle import TriangleSkiaRenderer

__all__ = [
    "ArcSkiaRenderer",
    "AstroidSkiaRenderer",
    "VertexSkiaRenderer",
    "CircleSkiaRenderer",
    "CircleTextSkiaRenderer",
    "EllipseSkiaRenderer",
    "ImageSkiaRenderer",
    "LineSkiaRenderer",
    "NumberSkiaRenderer",
    "PathSkiaRenderer",
    "PathAndTextVariantsSkiaRenderer",
    "PathBandSkiaRenderer",
    "PathTextSkiaRenderer",
    "PathVariantsSkiaRenderer",
    "PolygonSkiaRenderer",
    "RadialSegmentsSkiaRenderer",
    "RawSvgSkiaRenderer",
    "RectangleSkiaRenderer",
    "RingSkiaRenderer",
    "SquareSkiaRenderer",
    "StarSkiaRenderer",
    "StateCollectionSkiaRenderer",
    "TextSkiaRenderer",
    "TextPathSkiaRenderer",
    "TriangleSkiaRenderer",
]
