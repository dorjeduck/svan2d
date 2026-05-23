"""Skia renderer for ImageState — faithful mirror of ImageRenderer."""

from __future__ import annotations

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
        if state.opacity < 1.0:
            paint.setAlphaf(state.opacity)
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
        key = id(state)
        cached = ctx.images.get(key)
        if cached is not None:
            return cached
        if state.data is not None:
            img = skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(state.data))
        else:
            img = skia.Image.open(state.href)
        if img is None:
            raise SkiaUnsupported(f"Image could not be decoded by Skia: {state.href!r}")
        ctx.images[key] = img
        return img
