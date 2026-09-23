"""Clipping and masking for the Skia backend, as offscreen layers.

The content is drawn into a layer; each mask and the clip are then drawn into
their own layers and composited onto it with DstIn, which keeps the content
only where the clip or mask has coverage. Any state with a Skia renderer can
therefore clip or mask, with no need to turn shapes into paths:

- Clip: the clip shapes' union, drawn solid (fill forced opaque, no stroke, no
  opacity), since an SVG clipPath uses the raw geometry of its children.
- Mask: the mask shape drawn as it is, its luminance times its alpha becoming
  the coverage (LumaColorFilter), as an SVG luminance mask does. Several masks
  apply one after another, so their coverages multiply.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Callable, Sequence

import skia

from svan2d.core.color import Color
from svan2d.primitive.registry import get_skia_renderer_for_state

if TYPE_CHECKING:
    from svan2d.primitive.state.base import State
    from svan2d.skia.base import SkiaContext

_BLACK = Color("#000000")
_WHITE = Color("#FFFFFF")


def clip_states_of(state: "State") -> list["State"]:
    if state.clip_state is not None:
        return [state.clip_state]
    return list(state.clip_states or [])


def mask_states_of(state: "State") -> list["State"]:
    if state.mask_state is not None:
        return [state.mask_state]
    return list(state.mask_states or [])


def draw_clipped(
    canvas: skia.Canvas,
    draw: Callable[[], None],
    clips: Sequence["State"],
    masks: Sequence["State"],
    ctx: "SkiaContext",
) -> None:
    """Run draw() with the clips and masks applied, as Renderer's
    _create_clip_path_def and _create_mask_def build them."""
    if not clips and not masks:
        draw()
        return

    canvas.saveLayer(None, None)
    try:
        draw()
        for mask in masks:
            if _has_no_fill(mask):
                mask = _replace_fields(mask, fill_color=_WHITE)
            paint = skia.Paint(
                BlendMode=skia.BlendMode.kDstIn,
                ColorFilter=skia.LumaColorFilter.Make(),
            )
            canvas.saveLayer(None, paint)
            try:
                _draw_shape(canvas, mask, ctx)
            finally:
                canvas.restore()
        if clips:
            canvas.saveLayer(None, skia.Paint(BlendMode=skia.BlendMode.kDstIn))
            try:
                for clip in clips:
                    _draw_shape(canvas, _solid(clip), ctx)
            finally:
                canvas.restore()
    finally:
        canvas.restore()


def _draw_shape(canvas: skia.Canvas, state: "State", ctx: "SkiaContext") -> None:
    """Draw a clip or mask shape: its own transform and opacity, then its geometry."""
    from svan2d.skia.base import SkiaRenderer

    renderer = get_skia_renderer_for_state(state)
    canvas.save()
    try:
        SkiaRenderer._apply_transform(canvas, state)
        opacity = state.opacity if state.opacity is not None else 1.0
        if opacity < 1.0:
            canvas.saveLayerAlpha(None, int(round(opacity * 255)))
            try:
                renderer.draw_core(canvas, state, ctx)
            finally:
                canvas.restore()
        else:
            renderer.draw_core(canvas, state, ctx)
    finally:
        canvas.restore()


def _solid(state: "State") -> "State":
    """The state as a clip shape: its geometry filled opaque, nothing else."""
    return _replace_fields(
        state,
        fill_color=_BLACK,
        fill_opacity=1.0,
        stroke_width=0,
        opacity=1.0,
        fill_gradient=None,
        fill_pattern=None,
        stroke_gradient=None,
        stroke_pattern=None,
    )


def _has_no_fill(state: "State") -> bool:
    fill = getattr(state, "fill_color", None)
    return fill is None or fill == Color.NONE


def _replace_fields(state: "State", **values) -> "State":
    """dataclasses.replace for just the fields this state has."""
    names = {f.name for f in dataclasses.fields(state)}
    return dataclasses.replace(state, **{k: v for k, v in values.items() if k in names})
