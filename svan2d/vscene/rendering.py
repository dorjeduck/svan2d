"""Rendering and clipping functions for VScene."""

from __future__ import annotations

from typing import TYPE_CHECKING

import drawsvg as dw

if TYPE_CHECKING:
    from svan2d.component.state.base import State


def build_scene_transform(
    scale: float,
    rotation: float,
    offset_x: float,
    offset_y: float,
    render_scale: float,
) -> str:
    """Build SVG transform string from scene transforms.

    Returns:
        SVG transform string, or empty string if no transforms needed
    """
    transforms = []

    total_scale = scale * render_scale
    if total_scale != 1.0:
        transforms.append(f"scale({total_scale})")

    if rotation != 0.0:
        transforms.append(f"rotate({rotation})")

    if offset_x != 0.0 or offset_y != 0.0:
        transforms.append(f"translate({offset_x},{offset_y})")

    return " ".join(transforms)


def apply_scene_clipping(
    group: dw.Group,
    drawing: dw.Drawing,
    clip_state: "State | None",
    mask_state: "State | None",
) -> dw.Group:
    """Apply scene-level clip/mask to root group.

    Uses the same clipping logic as Renderer._apply_clipping_and_masking
    but at the scene level.
    """
    import uuid

    from svan2d.component import get_renderer_instance_for_state

    result = group

    # Apply mask first (innermost)
    if mask_state is not None:
        mask_id = f"mask-{uuid.uuid4().hex[:8]}"
        mask = dw.Mask(id=mask_id)

        renderer = get_renderer_instance_for_state(mask_state)
        mask_elem = renderer._render_core(mask_state, drawing=drawing)

        transforms = []
        if mask_state.x != 0 or mask_state.y != 0:
            transforms.append(f"translate({mask_state.x},{mask_state.y})")
        if mask_state.rotation != 0:
            transforms.append(f"rotate({mask_state.rotation})")
        if mask_state.scale != 1.0:
            transforms.append(f"scale({mask_state.scale})")

        mask_group = dw.Group(opacity=mask_state.opacity)
        if transforms:
            mask_group.args["transform"] = " ".join(transforms)
        mask_group.append(mask_elem)
        mask.append(mask_group)

        drawing.append_def(mask)

        masked_group = dw.Group(mask=f"url(#{mask_id})")
        masked_group.append(result)
        result = masked_group

    # Apply clip
    if clip_state is not None:
        clip_id = f"clip-{uuid.uuid4().hex[:8]}"
        clip_path = dw.ClipPath(id=clip_id)

        renderer = get_renderer_instance_for_state(clip_state)
        clip_elem = renderer._render_core(clip_state, drawing=drawing)

        if (
            clip_state.x != 0
            or clip_state.y != 0
            or clip_state.rotation != 0
            or clip_state.scale != 1.0
        ):
            transforms = []
            if clip_state.x != 0 or clip_state.y != 0:
                transforms.append(
                    f"translate({clip_state.x},{clip_state.y})"
                )
            if clip_state.rotation != 0:
                transforms.append(f"rotate({clip_state.rotation})")
            if clip_state.scale != 1.0:
                transforms.append(f"scale({clip_state.scale})")
            clip_group = dw.Group(transform=" ".join(transforms))
            clip_group.append(clip_elem)
            clip_path.append(clip_group)
        else:
            clip_path.append(clip_elem)

        drawing.append_def(clip_path)

        clipped_group = dw.Group(clip_path=f"url(#{clip_id})")
        clipped_group.append(result)
        result = clipped_group

    return result
