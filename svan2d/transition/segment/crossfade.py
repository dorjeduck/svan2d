"""Crossfade segment function (multi-element)."""

from dataclasses import replace
from typing import Callable, Dict, List, Optional, Tuple

from svan2d.component.state.base import State
from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig


def crossfade(
    s_out: State,
    s_in: State,
    t_start: float,
    t_end: float,
    delay: Optional[float] = 0,
    easing_dict: Optional[Dict[str, Callable[[float], float]]] = None,
) -> Tuple[List[KeyState], List[KeyState]]:
    """Fades one element out while fading a second element in simultaneously.

    Args:
        s_out: The State of the element that will fade OUT.
        s_in: The State of the element that will fade IN.
        t_start: The absolute time (normalized to [0, 1]) when the crossfade begins.
        t_end: The absolute time (normalized to [0, 1]) when the crossfade ends.
        delay: delay between fade out and fade in
        easing: Optional easing dict for opacity transitions.

    Returns:
        Tuple of (keystates_for_fading_in, keystates_for_fading_out)
    """
    transition = TransitionConfig(easing_dict=easing_dict) if easing_dict else None

    # --- Element Fading IN (starts invisible, ends as s_in) ---
    s_in_gone = replace(s_in, opacity=0.0)

    keystates_in = [
        # Start invisible
        KeyState(
            state=s_in_gone, time=max(0, t_start + (delay or 0)), transition_config=transition
        ),
        # End visible
        KeyState(state=s_in, time=min(1, t_end)),
    ]

    s_out_gone = replace(s_out, opacity=0.0)

    keystates_out = [
        # Start visible
        KeyState(state=s_out, time=max(0, t_start), transition_config=transition),
        # End invisible
        KeyState(state=s_out_gone, time=min(1, t_end - (delay or 0))),
    ]

    return keystates_out, keystates_in
