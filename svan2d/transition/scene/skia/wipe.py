"""Skia version of Wipe: each scene clipped to its side of a moving edge."""

from __future__ import annotations

import skia

from svan2d.skia.base import SkiaSceneTransition
from svan2d.transition.scene.skia._common import clipped_to, draw_background


class WipeSkia(SkiaSceneTransition):
    def draw(self, canvas, transition, scene_out, scene_in, draw_out, draw_in, progress, ctx) -> None:
        bg_x, bg_y, width, height = transition._get_background_rect(ctx)
        draw_background(
            canvas,
            transition._get_background_color(scene_out, scene_in),
            (bg_x, bg_y, width, height),
        )
        out_rect, in_rect = transition._calculate_clip_rects(
            progress, bg_x, bg_y, width, height
        )
        clipped_to(canvas, skia.Path.Rect(skia.Rect.MakeXYWH(*out_rect)), draw_out)
        clipped_to(canvas, skia.Path.Rect(skia.Rect.MakeXYWH(*in_rect)), draw_in)
