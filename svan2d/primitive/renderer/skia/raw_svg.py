"""Skia renderer for RawSvgState — best-effort, via skia.SVGDOM.

Unlike the per-primitive renderers, this is not a faithful mirror: the SVG
payload is arbitrary, so it is handed to Skia's built-in SVG rasterizer
(skia.SVGDOM) rather than reconstructed primitive by primitive. SVGDOM covers
shapes, paths, fills/strokes, gradients and basic text, but not the full SVG
spec (filters and some advanced text features are unsupported), so output may
differ from the resvg/Playwright route for exotic fragments. A one-time warning
is logged the first time a raw_svg element is rendered through Skia.
"""

from __future__ import annotations

import skia

from svan2d.core.logger import get_logger
from svan2d.primitive.renderer.raw_svg import _counter_flip_orientation
from svan2d.primitive.state.raw_svg import RawSvgState
from svan2d.skia.base import SkiaContext, SkiaRenderer, SkiaUnsupported

_warned = False


class RawSvgSkiaRenderer(SkiaRenderer):
    """Best-effort raw-SVG renderer backed by skia.SVGDOM.

    Holds a one-slot cache of the parsed SVGDOM keyed on the identity of
    ``state.svg_data`` and the ``y_up`` flag (which rewrites the payload),
    mirroring the SVG renderer's caching so the DOM is reparsed only when the
    payload actually changes.
    """

    def __init__(self) -> None:
        self._cached_key: tuple[int, bool] | None = None
        self._cached_dom: skia.SVGDOM | None = None

    def draw_core(self, canvas, state: RawSvgState, ctx: SkiaContext) -> None:
        global _warned
        if not _warned:
            get_logger().warning(
                "raw_svg rendered via Skia's best-effort SVGDOM rasterizer; "
                "output may differ from the SVG backend for filters and some "
                "advanced text features."
            )
            _warned = True

        if not state.svg_data:
            return

        dom = self._dom(state)
        if ctx.scene_width > 0 and ctx.scene_height > 0:
            dom.setContainerSize(skia.Size(ctx.scene_width, ctx.scene_height))
        dom.render(canvas)

    def _dom(self, state: RawSvgState) -> skia.SVGDOM:
        key = (id(state.svg_data), bool(state.y_up))
        if key == self._cached_key and self._cached_dom is not None:
            return self._cached_dom

        svg_data = (
            _counter_flip_orientation(state.svg_data)
            if state.y_up
            else state.svg_data
        )
        # Wrap the fragment in a root <svg> so SVGDOM can parse it as a document.
        doc = f'<svg xmlns="http://www.w3.org/2000/svg">{svg_data}</svg>'
        dom = skia.SVGDOM.MakeFromStream(skia.MemoryStream(doc.encode("utf-8")))
        if dom is None:
            raise SkiaUnsupported("raw_svg payload could not be parsed by Skia")
        self._cached_key = key
        self._cached_dom = dom
        return dom
