"""Component system for svan2d - renderers and states for various shapes and elements"""

# Import submodules
from . import effect, renderer, state, vertex

# Import registry functions
from .registry import (
    clear_renderer_cache,
    get_all_registered_state_renderer_pairs,
    get_renderer_class_for_state,
    get_renderer_instance_for_state,
    is_renderer_registered_for_state,
)

# Import all renderers
from .renderer import *

# Import all states
from .state import *

# Import shape classes from perforated submodule
from .state.perforated import Astroid, Circle, Ellipse, Polygon, Rectangle, Shape, Star

# Import vertex classes
from .vertex import *

# Import effects
from .effect import *

__all__ = [
    # Submodules
    "renderer",
    "state",
    "vertex",
    # Registry functions
    "get_renderer_class_for_state",
    "is_renderer_registered_for_state",
    "get_all_registered_state_renderer_pairs",
    "get_renderer_instance_for_state",
    "clear_renderer_cache",
    # Base classes
    "Renderer",
    "State",
    "VertexState",
    "VertexRenderer",
    "LineRenderer",
    # Vertex classes
    "VertexLoop",
    "VertexContours",
    "VertexEllipse",
    "VertexCircle",
    "VertexRectangle",
    "VertexLine",
    "VertexPolygon",
    # Shape classes
    "Shape",
    "Circle",
    "Ellipse",
    "Rectangle",
    "Polygon",
    "Star",
    "Astroid",
    # States (alphabetically sorted)
    "ArcState",
    "ArrowState",
    "AstroidState",
    "CircleState",
    "CircleTextState",
    "ColorState",
    "CrossState",
    "EllipseState",
    "FlowerState",
    "HeartState",
    "ImageState",
    "InfinityState",
    "LineState",
    "NumberState",
    "PathBandState",
    "PathState",
    "PathTextState",
    "PerforatedVertexState",
    "PerforatedCircleState",
    "PerforatedStarState",
    "PerforatedEllipseState",
    "PerforatedRectangleState",
    "PerforatedPolygonState",
    "PerforatedTriangleState",
    "PathAndTextVariantsState",
    "PathVariantsState",
    "PointState",
    "PolyRingState",
    "PolygonState",
    "RadialSegmentsState",
    "RawSvgState",
    "RectangleState",
    "RingState",
    "SpiralState",
    "SquareRingState",
    "SquareState",
    "StarState",
    "StateCollectionState",
    "TextPathState",
    "TextState",
    "TriangleState",
    "WaveState",
    # State support types
    "States",
    "ImageFitMode",
    "NumberFormat",
    "Rounding",
    "TextRendering",
    # Renderers (alphabetically sorted)
    "AstroidRenderer",
    "CircleRenderer",
    "CircleTextRenderer",
    "EllipseRenderer",
    "ImageRenderer",
    "PathRenderer",
    "PathTextRenderer",
    "PerforatedPrimitiveRenderer",
    "PathAndTextVariantsRenderer",
    "PathVariantsRenderer",
    "PolyRingRenderer",
    "RadialSegmentsRenderer",
    "RawSvgRenderer",
    "RectangleRenderer",
    "RingRenderer",
    "SquareRingRenderer",
    "StarRenderer",
    "TextRenderer",
    "TriangleRenderer",
    # Effects - Gradients
    "Gradient",
    "LinearGradient",
    "RadialGradient",
    "GradientStop",
    # Effects - Patterns
    "Pattern",
    "CustomPattern",
    "DotsPattern",
    "StripesPattern",
    "GridPattern",
    "CheckerboardPattern",
    # Effects - Filters
    "Filter",
    "GaussianBlurFilter",
    "DropShadowFilter",
    "ColorMatrixFilter",
    "CompositeFilter",
    "OffsetFilter",
    "MorphologyFilter",
    "FloodFilter",
    "BlendFilter",
    "CompositeFilterPrimitive",
    "TurbulenceFilter",
    "DisplacementMapFilter",
    "ConvolveMatrixFilter",
    "TileFilter",
    "ImageFilter",
    "MergeNodeFilter",
]
