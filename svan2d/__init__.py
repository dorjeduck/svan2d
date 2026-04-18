"""Svan2D - SVG Animation Library

A Python library for creating beautiful SVG animations.

Re-exports commonly used symbols for convenient flat imports::

    from svan2d import VElement, VScene, VSceneExporter, Color, Point2D, layout, easing
"""

# --- Namespace modules (imported as submodules, not flattened) ---
from svan2d import layout
from svan2d.transition import curve, easing
from svan2d.transition.easing import easing2D

# --- Core ---
from svan2d.core import Color, Point2D, configure_logging, get_logger

# --- Converter ---
from svan2d.converter import ConverterType

# --- VElement ---
from svan2d.velement import (
    KeyState,
    MorphingConfig,
    TransitionConfig,
    VElement,
    VElementGroup,
    VElementGroupState,
    bounce,
    crossfade,
    fade_inout,
    hold,
    linspace,
)

# --- VScene ---
from svan2d.vscene import (
    CameraState,
    VScene,
    VSceneComposite,
    VSceneExporter,
    VSceneSequence,
)

# --- Primitive: states, renderers, effects ---
# States (from svan2d.primitive.state)

from svan2d.primitive.registry import renderer

from svan2d.primitive.state import (
    ArcState,
    ArrowState,
    AstroidState,
    CircleState,
    CircleTextState,
    ColorState,
    CrossState,
    EllipseState,
    FlowerState,
    HeartState,
    InfinityState,
    LineState,
    NumberFormat,
    NumberState,
    PathAndTextVariantsState,
    PathState,
    PathTextState,
    PerforatedCircleState,
    PerforatedEllipseState,
    PerforatedPolygonState,
    PerforatedRectangleState,
    PerforatedStarState,
    PerforatedTriangleState,
    PerforatedVertexState,
    PointState,
    PolyRingState,
    PolygonState,
    RadialSegmentsState,
    RawSvgState,
    RectangleState,
    RingState,
    Rounding,
    SpiralState,
    SquareRingState,
    SquareState,
    StarState,
    State,
    StateCollectionState,
    States,
    TextPathState,
    TextRendering,
    TextState,
    TriangleState,
    VertexState,
    WaveState,
)

# Perforated shapes
from svan2d.primitive.state.perforated import (
    Astroid,
    Circle,
    Ellipse,
    Polygon,
    Rectangle,
    Shape,
    Star,
)

# Renderers (from svan2d.primitive.renderer)
from svan2d.primitive.renderer import (
    ArcRenderer,
    ArrowRenderer,
    AstroidRenderer,
    CircleRenderer,
    CircleTextRenderer,
    CrossRenderer,
    EllipseRenderer,
    HeartRenderer,
    InfinityRenderer,
    NumberRenderer,
    PathAndTextVariantsRenderer,
    PathRenderer,
    PathTextRenderer,
    PerforatedPrimitiveRenderer,
    PointRenderer,
    PolyRingRenderer,
    PolygonRenderer,
    RawSvgRenderer,
    RectangleRenderer,
    Renderer,
    RingRenderer,
    SpiralRenderer,
    SquareRenderer,
    SquareRingRenderer,
    StateCollectionRenderer,
    TextRenderer,
    TriangleRenderer,
    VertexRenderer,
    WaveRenderer,
)

# Vertex geometry
from svan2d.primitive.vertex import (
    VertexCircle,
    VertexContours,
    VertexEllipse,
    VertexLine,
    VertexLoop,
    VertexPolygon,
    VertexRectangle,
)

# Effects - Gradients
from svan2d.primitive.effect.gradient import (
    Gradient,
    GradientStop,
    LinearGradient,
    RadialGradient,
)

# Effects - Patterns
from svan2d.primitive.effect.pattern import (
    CheckerboardPattern,
    CustomPattern,
    DotsPattern,
    GridPattern,
    Pattern,
    StripesPattern,
)

# Effects - Filters
from svan2d.utils.schedule import OverlapMode, WeightedSchedule
from svan2d.utils.stagger_schedule import StaggerDirection, StaggerSchedule

from svan2d.primitive.effect.filter import (
    BlendFilter,
    ColorMatrixFilter,
    CompositeFilter,
    CompositeFilterPrimitive,
    ConvolveMatrixFilter,
    DisplacementMapFilter,
    DropShadowFilter,
    Filter,
    FloodFilter,
    GaussianBlurFilter,
    ImageFilter,
    MergeNodeFilter,
    MorphologyFilter,
    OffsetFilter,
    TileFilter,
    TurbulenceFilter,
)

__version__ = "0.5.0-alpha"

__all__ = [
    # Namespace modules
    "layout",
    "easing",
    "easing2D",
    "curve",
    # Core
    "Color",
    "Point2D",
    "configure_logging",
    "get_logger",
    # Converter
    "ConverterType",
    # VElement
    "VElement",
    "VElementGroup",
    "VElementGroupState",
    "KeyState",
    "TransitionConfig",
    "MorphingConfig",
    "hold",
    "fade_inout",
    "bounce",
    "crossfade",
    "linspace",
    # VScene
    "VScene",
    "VSceneExporter",
    "VSceneSequence",
    "VSceneComposite",
    "CameraState",
    # Component - base
    "renderer",
    "Renderer",
    "State",
    "States",
    "ColorState",
    "VertexRenderer",
    "VertexState",
    "VertexContours",
    "VertexCircle",
    "VertexEllipse",
    "VertexLine",
    "VertexLoop",
    "VertexPolygon",
    "VertexRectangle",
    # States
    "ArcState",
    "ArrowState",
    "AstroidState",
    "CircleState",
    "CircleTextState",
    "CrossState",
    "EllipseState",
    "FlowerState",
    "HeartState",
    "InfinityState",
    "LineState",
    "NumberFormat",
    "NumberState",
    "PathAndTextVariantsState",
    "PathState",
    "PathTextState",
    "PerforatedCircleState",
    "PerforatedEllipseState",
    "PerforatedPolygonState",
    "PerforatedRectangleState",
    "PerforatedStarState",
    "PerforatedTriangleState",
    "PerforatedVertexState",
    "PointState",
    "PolyRingState",
    "PolygonState",
    "RadialSegmentsState",
    "RawSvgState",
    "RectangleState",
    "RingState",
    "Rounding",
    "SpiralState",
    "SquareRingState",
    "SquareState",
    "StarState",
    "StateCollectionState",
    "TextPathState",
    "TextRendering",
    "TextState",
    "TriangleState",
    "WaveState",
    # Perforated shapes
    "Astroid",
    "Circle",
    "Ellipse",
    "Polygon",
    "Rectangle",
    "Shape",
    "Star",
    # Renderers
    "ArcRenderer",
    "ArrowRenderer",
    "AstroidRenderer",
    "CircleRenderer",
    "CircleTextRenderer",
    "CrossRenderer",
    "EllipseRenderer",
    "HeartRenderer",
    "InfinityRenderer",
    "NumberRenderer",
    "PathAndTextVariantsRenderer",
    "PathRenderer",
    "PathTextRenderer",
    "PerforatedPrimitiveRenderer",
    "PointRenderer",
    "PolyRingRenderer",
    "PolygonRenderer",
    "RawSvgRenderer",
    "RectangleRenderer",
    "RingRenderer",
    "SpiralRenderer",
    "SquareRenderer",
    "SquareRingRenderer",
    "StateCollectionRenderer",
    "TextRenderer",
    "TriangleRenderer",
    "WaveRenderer",
    # Effects - Gradients
    "Gradient",
    "GradientStop",
    "LinearGradient",
    "RadialGradient",
    # Effects - Patterns
    "CheckerboardPattern",
    "CustomPattern",
    "DotsPattern",
    "GridPattern",
    "Pattern",
    "StripesPattern",
    # Utils
    "OverlapMode",
    "StaggerDirection",
    "StaggerSchedule",
    "WeightedSchedule",
    # Effects - Filters
    "BlendFilter",
    "ColorMatrixFilter",
    "CompositeFilter",
    "CompositeFilterPrimitive",
    "ConvolveMatrixFilter",
    "DisplacementMapFilter",
    "DropShadowFilter",
    "Filter",
    "FloodFilter",
    "GaussianBlurFilter",
    "ImageFilter",
    "MergeNodeFilter",
    "MorphologyFilter",
    "OffsetFilter",
    "TileFilter",
    "TurbulenceFilter",
]
