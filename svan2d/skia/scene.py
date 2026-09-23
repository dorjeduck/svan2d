"""Render a scene to a Skia surface (PNG), bypassing SVG.

draw_scene draws a VScene, VSceneComposite or VSceneSequence onto the canvas
as its to_drawing builds it: the canvas stands at the drawing's origin, in
output pixels, and render_scale, width and height mean what they mean there.
Composites and sequences draw their scenes through draw_scene again, so they
nest in each other as they do in SVG; a transition is drawn by the Skia version
its class registers (svan2d.transition.scene.registry). Anything this backend
does not implement is rejected up front by support.check_scene, so the render
loop performs no capability checks.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import skia

from svan2d.core.enums import Origin
from svan2d.skia.base import SkiaContext, SkiaRenderer, skia_color
from svan2d.skia.clipping import clip_states_of, draw_clipped, mask_states_of
from svan2d.primitive.registry import get_skia_renderer_for_state
from svan2d.transition.scene.base import RenderContext
from svan2d.transition.scene.registry import get_skia_transition

if TYPE_CHECKING:
    from svan2d.vscene.camera_state import CameraState
    from svan2d.vscene.vscene import VScene
    from svan2d.vscene.vscene_composite import VSceneComposite
    from svan2d.vscene.vscene_sequence import VSceneSequence


def render_scene_to_image(
    scene,
    frame_time: float,
    width_px: int,
    height_px: int,
    ctx: SkiaContext | None = None,
) -> skia.Image:
    """Render one frame of a VScene, VSceneComposite or VSceneSequence to a
    skia.Image.

    The scene is fitted into the image at one scale, the smaller of the two,
    as SVGConverter does. Passing the same ctx for every frame keeps fonts and
    images loaded from one frame to the next.
    """
    if not 0.0 <= frame_time <= 1.0:
        raise ValueError(f"frame_time must be in [0,1], got {frame_time}")

    surface = skia.Surface(int(width_px), int(height_px))
    canvas = surface.getCanvas()
    canvas.clear(skia.Color4f.kTransparent)

    render_scale = min(width_px / scene.width, height_px / scene.height)
    if scene.origin == Origin.CENTER:
        canvas.translate(width_px / 2, height_px / 2)
    ctx = ctx if ctx is not None else SkiaContext()
    draw_scene(canvas, scene, frame_time, ctx, render_scale, width_px, height_px)
    ctx.end_frame()

    return surface.makeImageSnapshot()


def draw_scene(
    canvas: skia.Canvas,
    scene,
    frame_time: float,
    ctx: SkiaContext,
    render_scale: float = 1.0,
    width: float | None = None,
    height: float | None = None,
) -> None:
    """Draw a VScene, VSceneComposite or VSceneSequence as its to_drawing
    would build it."""
    from svan2d.vscene.vscene_composite import VSceneComposite
    from svan2d.vscene.vscene_sequence import VSceneSequence

    if isinstance(scene, VSceneComposite):
        _draw_composite(canvas, scene, frame_time, ctx, render_scale, width, height)
    elif isinstance(scene, VSceneSequence):
        _draw_sequence(canvas, scene, frame_time, ctx, render_scale)
    else:
        _draw_vscene(canvas, scene, frame_time, ctx, render_scale, width, height)


def _draw_background(canvas, color, opacity: float, origin, ww: float, hh: float) -> None:
    # `if color` rather than `is not None`: the default background is
    # Color.NONE, which is an object but falsy, and painting it would fill the
    # canvas with opaque black instead of leaving it transparent.
    if not color or opacity <= 0.0:
        return
    x, y = (-ww / 2, -hh / 2) if origin == Origin.CENTER else (0.0, 0.0)
    canvas.drawRect(skia.Rect.MakeXYWH(x, y, ww, hh), skia.Paint(Color=skia_color(color, opacity)))


def _draw_vscene(
    canvas, scene: "VScene", frame_time: float, ctx: SkiaContext,
    render_scale: float, width: float | None, height: float | None,
) -> None:
    if not 0.0 <= frame_time <= 1.0:
        raise ValueError(f"frame_time must be in [0,1], got {frame_time}")
    if scene.reverse:
        frame_time = 1.0 - frame_time
    effective_easing, _ = scene._resolve_pause_easing()
    if effective_easing is not None:
        frame_time = effective_easing(frame_time)

    ww = width if width is not None else render_scale * scene.width
    hh = height if height is not None else render_scale * scene.height
    _draw_background(canvas, scene.background, scene.background_opacity, scene.origin, ww, hh)

    # raw_svg sizes its SVGDOM container by the scene it is drawn in; the
    # caches stay shared.
    ctx = dataclasses.replace(ctx, scene_width=scene.width, scene_height=scene.height)

    # A camera on a top-left scene with an animated offset centres the offset
    # point in the viewport.
    needs_centering = scene.origin != Origin.CENTER and scene._camera_offset_func is not None
    viewport = (ww / render_scale, hh / render_scale) if needs_centering else (0.0, 0.0)

    def draw_content() -> None:
        canvas.save()
        try:
            _apply_camera(canvas, scene._get_camera_state_at_time(frame_time), *viewport)
            _draw_children(canvas, scene.elements, frame_time, ctx)
        finally:
            canvas.restore()

    canvas.save()
    try:
        # Output scale around everything, then the clip/mask outside the
        # camera: to_drawing's nesting.
        canvas.scale(render_scale, render_scale)
        draw_clipped(
            canvas,
            draw_content,
            [scene.clip_state] if scene.clip_state is not None else [],
            [scene.mask_state] if scene.mask_state is not None else [],
            ctx,
        )
    finally:
        canvas.restore()


def _apply_camera(canvas, state: "CameraState", viewport_w: float, viewport_h: float) -> None:
    """camera.build_camera_transform (at render scale 1) as canvas operations."""
    assert state.scale is not None and state.pivot is not None and state.rotation is not None
    if viewport_w or viewport_h:
        canvas.translate(viewport_w / 2, viewport_h / 2)
    pivot = state.pivot
    around_pivot = (pivot.x != 0 or pivot.y != 0) and (state.scale != 1.0 or state.rotation != 0)
    if around_pivot:
        canvas.translate(pivot.x, -pivot.y)
    if state.scale != 1.0:
        canvas.scale(state.scale, state.scale)
    if state.rotation != 0:
        canvas.rotate(-state.rotation)
    if around_pivot:
        canvas.translate(-pivot.x, pivot.y)
    if state.x != 0 or state.y != 0:
        canvas.translate(-state.x, state.y)


def _draw_composite(
    canvas, composite: "VSceneComposite", frame_time: float, ctx: SkiaContext,
    render_scale: float, width: float | None, height: float | None,
) -> None:
    """VSceneComposite.to_drawing's layout, each child drawn by draw_scene."""
    if not 0.0 <= frame_time <= 1.0:
        raise ValueError(f"frame_time must be in [0,1], got {frame_time}")

    origin = composite.origin
    final_width = width if width is not None else composite.width * render_scale
    final_height = height if height is not None else composite.height * render_scale
    background = composite.background
    _draw_background(canvas, background, 1.0, origin, final_width, final_height)

    direction = composite.direction
    if direction == "overlay":
        offset = 0.0
    elif origin == Origin.CENTER:
        total = composite.width if direction == "horizontal" else composite.height
        offset = -total / 2 * render_scale
    else:
        offset = 0.0
    # Children overlap by a pixel so antialiasing leaves no seam between them.
    overlap = 1 * render_scale
    scenes = composite.scenes

    for i, (scene, scale) in enumerate(zip(scenes, composite._scales)):
        total_scale = scale * render_scale
        child_w = scene.width * total_scale
        child_h = scene.height * total_scale

        if direction == "horizontal":
            child_top_x = offset
            child_top_y = -child_h / 2 if origin == Origin.CENTER else 0.0
            offset += child_w + composite.gap * render_scale
            if i < len(scenes) - 1:
                offset -= overlap
        elif direction == "vertical":
            child_top_x = -child_w / 2 if origin == Origin.CENTER else 0.0
            child_top_y = offset
            offset += child_h + composite.gap * render_scale
            if i < len(scenes) - 1:
                offset -= overlap
        elif origin == Origin.CENTER:
            child_top_x, child_top_y = -child_w / 2, -child_h / 2
        else:
            child_top_x = child_top_y = 0.0

        if Origin(scene.origin) == Origin.CENTER:
            tx, ty = child_top_x + child_w / 2, child_top_y + child_h / 2
        else:
            tx, ty = child_top_x, child_top_y

        canvas.save()
        try:
            canvas.translate(round(tx), round(ty))
            draw_scene(canvas, scene, frame_time, ctx, total_scale)
        finally:
            canvas.restore()


def _draw_sequence(
    canvas, sequence: "VSceneSequence", frame_time: float, ctx: SkiaContext,
    render_scale: float,
) -> None:
    """VSceneSequence.to_drawing: a scene at its time, or a transition drawn by
    its Skia version. Like to_drawing, it takes no width or height."""
    frame = sequence._frame_at(frame_time)

    if frame.transition is None:
        draw_scene(canvas, frame.scene, frame.time, ctx, render_scale)
        return

    render_ctx = RenderContext(
        width=sequence.width,
        height=sequence.height,
        render_scale=render_scale,
        origin=sequence.origin,
    )
    get_skia_transition(frame.transition).draw(
        canvas,
        frame.transition,
        frame.scene_out,
        frame.scene_in,
        lambda: draw_scene(canvas, frame.scene_out, frame.time_out, ctx, render_scale),
        lambda: draw_scene(canvas, frame.scene_in, frame.time_in, ctx, render_scale),
        frame.progress,
        render_ctx,
    )


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
    # A group applies its .clip()/.mask() attachments when it renders (its
    # get_frame leaves them out), at the time its children are drawn at.
    if group.clip_elements or group.mask_element:
        group_state = group._apply_velement_clips(group_state, group._last_frame_time)

    canvas.save()
    try:
        SkiaRenderer._apply_transform(canvas, group_state)
        opacity = getattr(group_state, "opacity", 1.0) or 1.0
        if opacity < 1.0:
            canvas.saveLayerAlpha(None, int(round(opacity * 255)))
        try:
            draw_clipped(
                canvas,
                lambda: _draw_children(canvas, group.elements, frame_time, ctx),
                clip_states_of(group_state),
                mask_states_of(group_state),
                ctx,
            )
        finally:
            if opacity < 1.0:
                canvas.restore()
    finally:
        canvas.restore()
