"""Bounding box computation for states.

Computes axis-aligned bounding boxes in world space for any State.
"""

from __future__ import annotations

import math

from svan2d.component.state.base import State
from svan2d.component.state.base_vertex import VertexState
from svan2d.core.point2d import Point2D


def state_bounds(state: State) -> tuple[float, float, float, float] | None:
    """Compute axis-aligned bounding box in world space.

    Returns (min_x, min_y, max_x, max_y) or None if bounds cannot be determined.
    """
    local = _local_bounds(state)
    if local is None:
        return None

    return _transform_bounds(local, state)


def _local_bounds(state: State) -> tuple[float, float, float, float] | None:
    """Get bounds in local space (centered at origin, before transforms)."""
    if isinstance(state, VertexState):
        return state.get_contours().bounds()

    # ImageState
    from svan2d.component.state.image import ImageState

    if isinstance(state, ImageState):
        w = state.width if state.width is not None else 0
        h = state.height if state.height is not None else 0
        if w == 0 and h == 0:
            return (0.0, 0.0, 0.0, 0.0)
        return (-w / 2, -h / 2, w / 2, h / 2)

    # TextState, RawSvgState, unknown: point at origin
    return (0.0, 0.0, 0.0, 0.0)


def _transform_bounds(
    local: tuple[float, float, float, float],
    state: State,
) -> tuple[float, float, float, float]:
    """Apply scale, rotation, and translation to local bounds."""
    min_x, min_y, max_x, max_y = local

    # Scale
    scale = state.scale if state.scale is not None else 1.0
    min_x *= scale
    min_y *= scale
    max_x *= scale
    max_y *= scale

    # Rotation: compute rotated AABB from corners
    rotation = state.rotation if state.rotation is not None else 0.0
    if rotation != 0.0:
        rad = math.radians(rotation)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        corners = [
            (min_x, min_y),
            (max_x, min_y),
            (max_x, max_y),
            (min_x, max_y),
        ]

        rotated_xs = []
        rotated_ys = []
        for cx, cy in corners:
            rotated_xs.append(cx * cos_r - cy * sin_r)
            rotated_ys.append(cx * sin_r + cy * cos_r)

        min_x = min(rotated_xs)
        min_y = min(rotated_ys)
        max_x = max(rotated_xs)
        max_y = max(rotated_ys)

    # Translate
    pos = state.pos if state.pos is not None else Point2D(0, 0)
    return (min_x + pos.x, min_y + pos.y, max_x + pos.x, max_y + pos.y)
