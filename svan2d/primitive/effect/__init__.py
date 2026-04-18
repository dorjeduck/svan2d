"""Visual effects for SVG components

This module provides visual effects that can be applied to components:
- Gradients: Linear and radial color gradients
- Patterns: Repeating texture patterns
- Filters: SVG filter effects (blur, shadow, morphology, etc.)
"""

from .filter import (
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
from .gradient import Gradient, GradientStop, LinearGradient, RadialGradient
from .pattern import (
    CheckerboardPattern,
    CustomPattern,
    DotsPattern,
    GridPattern,
    Pattern,
    StripesPattern,
)

__all__ = [
    # Gradients
    "Gradient",
    "LinearGradient",
    "RadialGradient",
    "GradientStop",
    # Patterns
    "Pattern",
    "CustomPattern",
    "DotsPattern",
    "StripesPattern",
    "GridPattern",
    "CheckerboardPattern",
    # Filters
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
