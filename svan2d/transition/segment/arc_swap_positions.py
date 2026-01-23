"""Swap positions segment functions (multi-element)."""

import math
from dataclasses import replace
from typing import Callable, Dict, List, Optional, Tuple

from svan2d.component.state.base import State
from svan2d.transition.curve.arc import arc_clockwise, arc_counterclockwise
from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig


def arc_swap_positions(
    state_1: State,
    state_2: State,
    t_start: float,
    t_end: float,
    clockwise: bool = True,
    arc_radius: float | None = None,
    easing: Optional[Dict[str, Callable[[float], float]]] = None,
) -> Tuple[List[KeyState], List[KeyState]]:
    """Swaps the positions of two elements along arc paths.

    Both elements travel along parallel arcs in the same direction to avoid
    collision. The arc radius must be at least half the distance between points.

    Args:
        state_1: The base State of the first element.
        state_2: The base State of the second element.
        t_start: Start time of the swap.
        t_end: End time of the swap.
        clockwise: Arc direction (default True).
        arc_radius: Arc radius. If None, defaults to distance between points.
        easing: Optional easing dict for position transitions.

    Returns:
        Tuple of (keystates_for_elem1, keystates_for_elem2)

    Example:
        ks1, ks2 = arc_swap_positions(circle1, square2, t_start=0.3, t_end=0.8)
        elem1 = VElement().segment(ks1)
        elem2 = VElement().segment(ks2)
    """
    # Calculate distance between positions
    assert state_1.pos is not None and state_2.pos is not None
    dx = state_2.pos.x - state_1.pos.x
    dy = state_2.pos.y - state_1.pos.y
    distance = math.sqrt(dx * dx + dy * dy)

    # Determine arc radius
    # arc_radius=None or 0 uses distance as default (nice curved arc)
    # Minimum is half distance (semicircle), but that's a degenerate case
    min_radius = distance / 2
    if arc_radius is None:
        radius = distance
    else:
        radius = max(arc_radius, min_radius)

    # Select arc direction (both elements use same direction to avoid collision)
    arc_func = arc_clockwise if clockwise else arc_counterclockwise
    path_func = arc_func(radius)

    # Build transition config
    transition = TransitionConfig(easing_dict=easing, curve_dict={"pos": path_func})

    # Final states with swapped positions
    s1_final = replace(state_1, pos=state_2.pos)
    s2_final = replace(state_2, pos=state_1.pos)

    keystates_for_elem1 = [
        KeyState(state=state_1, time=t_start, transition_config=transition),
        KeyState(state=s1_final, time=t_end),
    ]

    keystates_for_elem2 = [
        KeyState(state=state_2, time=t_start, transition_config=transition),
        KeyState(state=s2_final, time=t_end),
    ]

    return keystates_for_elem1, keystates_for_elem2
