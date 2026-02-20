"""Core utilities for svan2d.

Provides fundamental types and utilities:
- Color: Color representation with interpolation support
- Point2D: 2D point with vector operations
- Logging: Configurable logging system
- Scalar functions: lerp, angle, step, inbetween, circular_midpoint
"""

from .color import Color, ColorSpace, ColorTuple, color_to_oklab, oklab_to_color
from .enums import Origin
from .logger import (
    configure_logging,
    get_logger,
)
from .point2d import Point2D, Points2D
from .mutable_point2d import (
    MutablePoint2D,
    MutablePoint2DPool,
    get_pooled_point,
    reset_point_pool,
)
from .scalar_functions import (
    angle,
    circular_midpoint,
    inbetween,
    lerp,
    log_lerp,
    gaussian_smooth,
    gaussian_smooth_2d,
    step,
)

__all__ = [
    "Color",
    "ColorTuple",
    "ColorSpace",
    "Origin",
    "configure_logging",
    "get_logger",
    "Point2D",
    "Points2D",
    "MutablePoint2D",
    "MutablePoint2DPool",
    "get_pooled_point",
    "reset_point_pool",
    "color_to_oklab",
    "oklab_to_color",
    "lerp",
    "log_lerp",
    "angle",
    "step",
    "inbetween",
    "circular_midpoint",
    "gaussian_smooth",
    "gaussian_smooth_2d",
]
