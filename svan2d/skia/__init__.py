"""Skia canvas rendering backend (opt-in, PNG-only).

An alternative to the State -> Renderer -> drawsvg -> SVG -> rasterizer pipeline:
here State -> SkiaRenderer -> skia.Canvas draw calls -> PNG, bypassing SVG entirely.

This is much faster for image-heavy scenes (resvg-py spends ~1s per embedded image;
skia draws it in ~2ms). It is selected explicitly via ConverterType.SKIA and is NOT
the default. When a scene uses a feature the Skia backend does not implement
(filters, clip/mask, or an unregistered state), the converter falls back to the SVG
route and prints an info message.

A state declares its default Skia renderer with @skia_renderer("module:Class")
ON THE STATE CLASS (defined in svan2d.primitive.registry, alongside the drawsvg
@renderer), the dotted path keeping skia off the import path until resolved.
Custom state classes may override State.get_skia_renderer_class(); individual
elements may pass skia_renderer=... to VElement.
"""

from svan2d.skia.base import SkiaRenderer, SkiaContext, SkiaUnsupported
from svan2d.primitive.registry import skia_renderer, get_skia_renderer_for_state
from svan2d.skia.support import check_scene

__all__ = [
    "SkiaRenderer",
    "SkiaContext",
    "SkiaUnsupported",
    "skia_renderer",
    "get_skia_renderer_for_state",
    "check_scene",
]
