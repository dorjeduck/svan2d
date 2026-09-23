"""Skia renderer for ImageState — faithful mirror of ImageRenderer."""

from __future__ import annotations

import os

import skia

from svan2d.primitive.renderer.image import ImageFitMode
from svan2d.primitive.state.image import ImageState
from svan2d.skia.base import SkiaContext, SkiaRenderer, SkiaUnsupported


class ImageSkiaRenderer(SkiaRenderer):
    """Mirror of ImageRenderer: decoded bitmap centered, with fit modes."""

    def draw_core(self, canvas, state: ImageState, ctx: SkiaContext) -> None:
        img = self._image(state, ctx)
        iw, ih = img.width(), img.height()
        tw = state.width if state.width is not None else iw
        th = state.height if state.height is not None else ih

        paint = skia.Paint(AntiAlias=True)
        sampling = skia.SamplingOptions(skia.FilterMode.kLinear)
        src = skia.Rect.MakeWH(iw, ih)

        if state.fit_mode == ImageFitMode.FIT:  # contain, preserve aspect
            s = min(tw / iw, th / ih)
            dw_, dh_ = iw * s, ih * s
            dst = skia.Rect.MakeXYWH(-dw_ / 2, -dh_ / 2, dw_, dh_)
        else:  # FILL / STRETCH -> exact target box
            dst = skia.Rect.MakeXYWH(-tw / 2, -th / 2, tw, th)

        canvas.drawImageRect(
            img, src, dst, sampling, paint, skia.Canvas.kStrict_SrcRectConstraint
        )

    @staticmethod
    def _image(state: ImageState, ctx: SkiaContext) -> skia.Image:
        # Keyed by what the image is made from, so a state rebuilt every frame
        # still finds it: the bytes themselves, or the file as it is now (a
        # file rewritten under the same name is read again).
        if state.data is not None:
            data = state.data
            key = ("data", data)
            load = lambda: skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(data))
        else:
            href = state.href
            stat = os.stat(href)
            key = ("file", os.path.abspath(href), stat.st_mtime_ns, stat.st_size)
            load = lambda: skia.Image.open(href)
        img = ctx.image(key, load)
        if img is None:
            raise SkiaUnsupported(f"Image could not be decoded by Skia: {state.href!r}")
        return img
