"""Render a VScene to a Skia surface (PNG), bypassing SVG.

Mirrors VScene.to_drawing's coordinate setup, z-ordering and element/group
iteration so the raster output matches the SVG route. Any feature this backend
does not implement raises SkiaUnsupported, which the converter surfaces as a
detailed error (no automatic fallback).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import skia

from svan2d.core.enums import Origin
from svan2d.skia.base import SkiaContext, skia_color
from svan2d.primitive.registry import get_skia_renderer_for_state

if TYPE_CHECKING:
    from svan2d.vscene.vscene import VScene


def render_scene_to_image(
    scene: "VScene", frame_time: float, width_px: int, height_px: int
) -> skia.Image:
    """Render one frame to a skia.Image.

    Assumes the scene was already validated by support.check_scene (the caller
    does this once per export); the render loop performs no capability checks.
    """
    if not 0.0 <= frame_time <= 1.0:
        raise ValueError(f"frame_time must be in [0,1], got {frame_time}")

    if getattr(scene, "reverse", False):
        frame_time = 1.0 - frame_time
    effective_easing, _ = scene._resolve_pause_easing()
    if effective_easing is not None:
        frame_time = effective_easing(frame_time)

    surface = skia.Surface(int(width_px), int(height_px))
    canvas = surface.getCanvas()
    canvas.clear(skia.Color4f.kTransparent)

    # Background
    if scene.background is not None and scene.background_opacity > 0.0:
        bg = skia.Paint(Color=skia_color(scene.background, scene.background_opacity))
        canvas.drawRect(skia.Rect.MakeWH(width_px, height_px), bg)

    # Base transform: scene world coords -> pixels (match drawsvg origin).
    sx = width_px / scene.width
    sy = height_px / scene.height
    canvas.save()
    if scene.origin == Origin.CENTER:
        canvas.translate(width_px / 2, height_px / 2)
    canvas.scale(sx, sy)

    # Static camera offset/zoom (animated camera already rejected above).
    cam = scene._get_camera_state_at_time(frame_time)
    _apply_static_camera(canvas, cam)

    ctx = SkiaContext(scene_width=scene.width, scene_height=scene.height)
    _draw_children(canvas, scene.elements, frame_time, ctx)
    canvas.restore()

    return surface.makeImageSnapshot()


def _apply_static_camera(canvas: skia.Canvas, cam) -> None:
    if cam is None:
        return
    zoom = getattr(cam, "zoom", 1.0) or 1.0
    offset = getattr(cam, "offset", None)
    if zoom != 1.0:
        canvas.scale(zoom, zoom)
    if offset is not None and (offset.x or offset.y):
        canvas.translate(-offset.x, offset.y)


def _draw_children(canvas, elements, frame_time: float, ctx: SkiaContext) -> None:
    # Pre-compute states and sort by z_index (mirrors to_drawing).
    pairs = []
    for el in elements:
        state = el.get_frame(frame_time) if hasattr(el, "get_frame") else None
        pairs.append((el, state))
    pairs.sort(key=lambda p: (p[1].z_index if p[1] is not None else 0.0))

    for el, state in pairs:
        if state is None:
            continue
        if hasattr(el, "elements"):  # VElementGroup
            _draw_group(canvas, el, state, frame_time, ctx)
        else:
            renderer = getattr(el, "_skia_renderer", None) or get_skia_renderer_for_state(state)
            renderer.draw(canvas, state, ctx)


def _draw_group(canvas, group, group_state, frame_time: float, ctx: SkiaContext) -> None:
    from svan2d.skia.base import SkiaRenderer

    canvas.save()
    try:
        SkiaRenderer._apply_transform(canvas, group_state)
        opacity = getattr(group_state, "opacity", 1.0) or 1.0
        if opacity < 1.0:
            canvas.saveLayerAlpha(None, int(round(opacity * 255)))
            try:
                _draw_children(canvas, group.elements, frame_time, ctx)
            finally:
                canvas.restore()
        else:
            _draw_children(canvas, group.elements, frame_time, ctx)
    finally:
        canvas.restore()
