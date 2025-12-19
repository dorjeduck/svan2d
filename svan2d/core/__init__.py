"""Core utilities for svan2d.

Provides fundamental types and utilities:
- Color: Color representation with interpolation support
- Point2D: 2D point with vector operations
- Logging: Configurable logging system
"""

from .color import Color, ColorTuple, ColorSpace
from .logger import (
    configure_logging,
    get_logger,
)
from .point2d import Point2D, Points2D, new_point2d

__all__ = [
    "Color",
    "ColorTuple",
    "ColorSpace",
    "configure_logging",
    "get_logger",
    "Point2D",
    "Points2D",
    "new_point2d",
]
