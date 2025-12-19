"""SVG to raster/video conversion backends.

Provides multiple converter backends for SVG rasterization:
- CairoSVG: Pure Python, good quality
- Inkscape: High quality, requires Inkscape installed
- Playwright: Browser-based, excellent CSS support
- Playwright HTTP: Server-based Playwright for batch rendering
"""

from .converter_type import ConverterType

__all__ = [
    "ConverterType",
]
