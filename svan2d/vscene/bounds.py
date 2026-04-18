"""Scene bounding box computation.

Computes the union bounding box of all elements in a scene at a given time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svan2d.primitive.state.bounds import state_bounds

if TYPE_CHECKING:
    from svan2d.primitive.state.base import State
    from svan2d.vscene.vscene import VScene


def scene_bounds_at(
    scene: "VScene",
    t: float,
    exclude: list | None = None,
) -> tuple[float, float, float, float] | None:
    """Compute the union AABB of all scene elements at time t.

    Args:
        scene: The VScene to compute bounds for.
        t: Normalized time (0.0 to 1.0).
        exclude: Elements to skip when computing bounds.

    Returns:
        (min_x, min_y, max_x, max_y) or None if no elements have bounds.
    """
    exclude_set = set(id(e) for e in exclude) if exclude else None
    all_bounds: list[tuple[float, float, float, float]] = []
    _collect_bounds(scene.elements, t, all_bounds, exclude_set)

    if not all_bounds:
        return None

    return (
        min(b[0] for b in all_bounds),
        min(b[1] for b in all_bounds),
        max(b[2] for b in all_bounds),
        max(b[3] for b in all_bounds),
    )


def _is_visible(state: State) -> bool:
    """Check if a state has any visible content."""
    if state.opacity == 0:
        return False

    from svan2d.primitive.state.base_color import ColorState

    if isinstance(state, ColorState):
        if state.fill_opacity == 0 and state.stroke_opacity == 0:
            return False

    return True


def _collect_bounds(
    elements: list,
    t: float,
    out: list[tuple[float, float, float, float]],
    exclude: set[int] | None = None,
) -> None:
    """Recursively collect bounds from elements and groups."""
    from svan2d.velement.velement_group import VElementGroup

    for element in elements:
        if exclude and id(element) in exclude:
            continue
        if isinstance(element, VElementGroup):
            _collect_bounds(element.elements, t, out, exclude)
        else:
            frame_state = element.get_frame(t)
            if frame_state is None:
                continue
            if not _is_visible(frame_state):
                continue
            bounds = state_bounds(frame_state)
            if bounds is not None:
                out.append(bounds)
