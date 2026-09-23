"""Skia version of Fade: the two scenes crossfaded over a blended background."""

from __future__ import annotations

from svan2d.skia.base import SkiaSceneTransition
from svan2d.transition.scene.skia._common import draw_background, with_opacity


class FadeSkia(SkiaSceneTransition):
    def draw(self, canvas, transition, scene_out, scene_in, draw_out, draw_in, progress, ctx) -> None:
        draw_background(
            canvas,
            transition._get_interpolated_background(scene_out, scene_in, progress),
            transition._get_background_rect(ctx),
        )
        opacity_out = 1.0 - progress
        opacity_in = progress
        if opacity_out > 0:
            with_opacity(canvas, opacity_out, draw_out)
        if opacity_in > 0:
            with_opacity(canvas, opacity_in, draw_in)
