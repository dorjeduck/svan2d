"""Helpers shared by the Skia scene transitions."""

from __future__ import annotations

from typing import Callable

import skia

from svan2d.skia.base import skia_color


def draw_background(canvas: skia.Canvas, color, rect: tuple[float, float, float, float]) -> None:
    """The solid rect composite() lays under the scenes, if it has a color.

    Color.NONE is falsy and becomes fill="none" in SVG, which draws nothing;
    the SVG rect sets no opacity, so the color is drawn opaque.
    """
    if color:
        canvas.drawRect(skia.Rect.MakeXYWH(*rect), skia.Paint(Color=skia_color(color)))


def with_opacity(canvas: skia.Canvas, opacity: float, draw: Callable[[], None]) -> None:
    """draw() as the content of a group with this opacity."""
    if opacity >= 1.0:
        draw()
        return
    canvas.saveLayerAlpha(None, int(round(opacity * 255)))
    try:
        draw()
    finally:
        canvas.restore()


def clipped_to(canvas: skia.Canvas, path: skia.Path, draw: Callable[[], None]) -> None:
    """draw() as the content of a group with this clip path."""
    canvas.save()
    try:
        canvas.clipPath(path, skia.ClipOp.kIntersect, True)
        draw()
    finally:
        canvas.restore()


def translated(canvas: skia.Canvas, dx: float, dy: float, draw: Callable[[], None]) -> None:
    canvas.save()
    try:
        canvas.translate(dx, dy)
        draw()
    finally:
        canvas.restore()
