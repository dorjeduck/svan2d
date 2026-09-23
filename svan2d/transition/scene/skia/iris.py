"""Skia version of Iris: one scene revealed or hidden by a circle."""

from __future__ import annotations

import math

import skia

from svan2d.skia.base import SkiaSceneTransition
from svan2d.transition.scene.skia._common import clipped_to


class IrisSkia(SkiaSceneTransition):
    def draw(self, canvas, transition, scene_out, scene_in, draw_out, draw_in, progress, ctx) -> None:
        _, _, width, height = transition._get_background_rect(ctx)
        if transition.center is not None:
            center_x, center_y = transition.center
        elif ctx.origin == "center":
            center_x, center_y = 0, 0
        else:
            center_x, center_y = width / 2, height / 2
        max_radius = math.sqrt(
            (width / 2 + abs(center_x)) ** 2 + (height / 2 + abs(center_y)) ** 2
        )

        if transition.direction == "open":
            radius = max_radius * progress
            below, clipped = draw_out, draw_in
        else:  # close
            radius = max_radius * (1 - progress)
            below, clipped = draw_in, draw_out

        below()
        clipped_to(canvas, skia.Path.Circle(center_x, center_y, radius), clipped)
