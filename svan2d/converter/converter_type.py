"""SVG converter backend type enumeration."""

from enum import StrEnum


class ConverterType(StrEnum):
    """
    Available SVG-to-raster converter backends.

    Members:
        PLAYWRIGHT_HTTP: Uses Playwright via HTTP for rendering.
        PLAYWRIGHT: Uses local Playwright instance for rendering.
        CAIROSVG: Uses CairoSVG library for conversion.
        INKSCAPE: Uses Inkscape command-line tool.
        IMAGEMAGICK: Uses ImageMagick command-line tool.
        RESVG: Uses the Rust `resvg` library via `resvg-py` (PNG only).
        RESVG_HTTP: Uses the resvg HTTP render server (PNG only).
    """

    PLAYWRIGHT_HTTP = "playwright_http"
    PLAYWRIGHT = "playwright"
    CAIROSVG = "cairosvg"
    INKSCAPE = "inkscape"
    IMAGEMAGICK = "imagemagick"
    RESVG = "resvg"
    RESVG_HTTP = "resvg_http"
