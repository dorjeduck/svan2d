"""SVG filters as Skia image filters.

A filtered state is drawn into a layer whose paint carries the filter, so the
filter sees the state's finished pixels, as an SVG filter sees SourceGraphic.
Only the filters listed in `supports_filter` have a Skia version; check_scene
reports every other one before any frame is drawn.

SVG filters work in linearRGB unless told otherwise, and svan2d does not tell
them otherwise, so a colour a filter writes as a constant is a linear value
that the browser turns back into sRGB. The Skia version converts that colour
itself, so both draw the same pixels.
"""

from __future__ import annotations

import skia

from svan2d.primitive.effect.filter import Filter
from svan2d.primitive.effect.filter.glow import GlowFilter


def supports_filter(filter_: Filter) -> bool:
    """Whether `image_filter` can turn this filter into a Skia image filter."""
    return isinstance(filter_, GlowFilter)


def image_filter(filter_: Filter) -> skia.ImageFilter:
    """The Skia image filter drawing what `filter_` draws in SVG."""
    if isinstance(filter_, GlowFilter):
        return _glow(filter_)
    raise TypeError(f"no Skia version of {type(filter_).__name__}")


def _glow(glow: GlowFilter) -> skia.ImageFilter:
    """GlowFilter's blur, colour matrix and merge, step for step.

    The SVG blurs SourceAlpha; blurring the source itself comes to the same,
    as the colour matrix after it reads only the alpha.
    """
    r, g, b = (
        (glow.color.r, glow.color.g, glow.color.b) if glow.color else (255, 255, 255)
    )
    red, green, blue = (_linear_to_srgb(c / 255.0) for c in (r, g, b))
    alpha_scale = glow.intensity * glow.opacity
    blur = skia.ImageFilters.Blur(glow.std_deviation, glow.std_deviation)
    colorize = skia.ImageFilters.ColorFilter(
        skia.ColorFilters.Matrix(
            [
                0, 0, 0, 0, red,
                0, 0, 0, 0, green,
                0, 0, 0, 0, blue,
                0, 0, 0, alpha_scale, 0,
            ]
        ),
        blur,
    )
    return skia.ImageFilters.Merge([colorize, None])


def _linear_to_srgb(c: float) -> float:
    """One channel, 0 to 1, from linearRGB to sRGB."""
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * c ** (1 / 2.4) - 0.055
