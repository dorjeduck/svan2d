"""Fade out segment function (single-element)."""

from dataclasses import replace
from typing import List, Optional, Callable, Dict, Tuple

from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig
from svan2d.component.state.base import State


def fade_out(
    s_in: State,
    at: float,
    dur: float,
    easing: Optional[Dict[str, Callable[[float], float]]] = None,
) -> List[KeyState]:
    """Fade an element out (visible to invisible).

    Returns a list of keystates for a single VElement.

    Args:
        s_in: State of the element (will fade to opacity 0)
        at: Start time of the fade out
        dur: Duration of the fade out
        easing: Optional easing dict for opacity transitions

    Returns:
        List of keystates (out_keystates)

    Example:
        out_ks = fade_out(circle, at=0.3, dur=0.2)
        elem_out = VElement().segment(out_ks)
    """
    transition = TransitionConfig(easing=easing) if easing else None

    # Element: visible -> invisible
    # Ensure the starting opacity is correctly set from the State or defaults to 1.0
    s_visible = replace(
        s_in, opacity=s_in.opacity if hasattr(s_in, "opacity") else 1.0
    )
    # The ending state is the same as the start, but with opacity 0.0
    s_gone = replace(s_in, opacity=0.0)

    # KeyState at the start of the fade (fully visible)
    # The time is set to start *before* the visible state if the transition starts
    # *at* a specific time, but for a simple fade, setting the start time of the
    # transition itself to `at` and the end time to `at + dur` is often clearer.
    # Following the crossfade structure (using a duration before and after 'at'):
    out_keystates = [
        # Start fully visible at `at - dur / 2`
        # Note: If `s_in` already has a valid transition, this will use it.
        KeyState(state=s_visible, time=at - dur / 2, transition_config=transition),
        # End completely gone at `at + dur / 2`
        KeyState(state=s_gone, time=min(1, at + dur / 2)),
    ]

    return out_keystates