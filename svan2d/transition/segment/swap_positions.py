"""Swap positions segment function (multi-element)."""

from dataclasses import replace
from typing import Callable, Dict, List, Optional, Tuple

from svan2d.component.state.base import State
from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig


def swap_positions(
    state_1: State,
    state_2: State,
    t_start: float,
    t_end: float,
    easing: Optional[Dict[str, Callable[[float], float]]] = None,
) -> Tuple[List[KeyState], List[KeyState]]:
    """Swaps the positions of two elements with linear interpolation.

    Returns two keystate lists for two separate VElements. This function assumes
    both State objects have a 'pos' attribute of type Point2D.

    Args:
        state_1: The base State of the first element.
        state_2: The base State of the second element.
        t_start: Start time of the swap.
        t_end: End time of the swap.
        easing: Optional easing dict for position transitions.

    Returns:
        Tuple of (keystates_for_elem1, keystates_for_elem2)

    Example:
        ks1, ks2 = swap_positions(circle1, square2, t_start=0.3, t_end=0.8)
        elem1 = VElement().segment(ks1)
        elem2 = VElement().segment(ks2)
    """
    transition = TransitionConfig(easing_dict=easing) if easing else None

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
