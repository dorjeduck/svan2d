"""Rendering and clipping functions for VScene."""

from __future__ import annotations

from typing import TYPE_CHECKING

import drawsvg as dw

if TYPE_CHECKING:
    from svan2d.primitive.state.base import State


def apply_scene_clipping(
    group: dw.Group,
    drawing: dw.Drawing,
    clip_state: "State | None",
    mask_state: "State | None",
) -> dw.Group:
    """Apply scene-level clip/mask to root group.

    Builds the clip and mask exactly as Renderer._apply_clipping_and_masking
    does for an element: the same shapes, fills and placement, only around the
    whole scene.
    """
    from svan2d.primitive.renderer.base import Renderer

    result = group

    # Apply mask first (innermost)
    if mask_state is not None:
        mask_id = Renderer._create_mask_def(mask_state, drawing)
        masked_group = dw.Group(mask=f"url(#{mask_id})")
        masked_group.append(result)
        result = masked_group

    # Apply clip
    if clip_state is not None:
        clip_id = Renderer._create_clip_path_def([clip_state], drawing)
        clipped_group = dw.Group(clip_path=f"url(#{clip_id})")
        clipped_group.append(result)
        result = clipped_group

    return result
