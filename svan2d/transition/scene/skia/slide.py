"""Skia version of Slide: the scenes moved across by the transition's offsets."""

from __future__ import annotations

from svan2d.skia.base import SkiaSceneTransition
from svan2d.transition.scene.skia._common import translated


class SlideSkia(SkiaSceneTransition):
    def draw(self, canvas, transition, scene_out, scene_in, draw_out, draw_in, progress, ctx) -> None:
        _, _, width, height = transition._get_background_rect(ctx)
        out_offset, in_offset = transition._calculate_offsets(progress, width, height)
        translated(canvas, *out_offset, draw_out)
        translated(canvas, *in_offset, draw_in)
