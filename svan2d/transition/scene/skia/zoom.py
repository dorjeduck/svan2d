"""Skia version of Zoom: the scenes scaled about the centre while they crossfade."""

from __future__ import annotations

from svan2d.skia.base import SkiaSceneTransition
from svan2d.transition.scene.skia._common import draw_background, with_opacity


class ZoomSkia(SkiaSceneTransition):
    def draw(self, canvas, transition, scene_out, scene_in, draw_out, draw_in, progress, ctx) -> None:
        bg_x, bg_y, width, height = transition._get_background_rect(ctx)
        draw_background(
            canvas,
            transition._get_interpolated_background(scene_out, scene_in, progress),
            (bg_x, bg_y, width, height),
        )
        if ctx.origin == "center":
            center_x, center_y = 0, 0
        else:
            center_x, center_y = width / 2, height / 2

        out_scale, in_scale = transition._calculate_scales(progress)
        for opacity, scale, draw in (
            (1.0 - progress, out_scale, draw_out),
            (progress, in_scale, draw_in),
        ):
            if opacity <= 0:
                continue
            canvas.save()
            try:
                canvas.translate(center_x, center_y)
                canvas.scale(scale, scale)
                canvas.translate(-center_x, -center_y)
                with_opacity(canvas, opacity, draw)
            finally:
                canvas.restore()
