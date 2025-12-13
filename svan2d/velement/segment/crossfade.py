"""Crossfade segment function (multi-element)."""

from dataclasses import replace
from typing import List, Optional, Callable, Dict, Tuple

from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig
from svan2d.component.state.base import State


def crossfade(
    s_out: State,
    s_in: State,
    at: float,
    dur: float,
    easing: Optional[Dict[str, Callable[[float], float]]] = None,
) -> Tuple[List[KeyState], List[KeyState]]:
    """Crossfade between two elements (one fading out, one fading in).

    Returns two keystate lists for two separate VElements.

    Args:
        s_out: State of the outgoing element (will fade to opacity 0)
        s_in: State of the incoming element (will fade from opacity 0)
        at: Start time of the crossfade
        dur: Duration of the crossfade
        easing: Optional easing dict for opacity transitions

    Returns:
        Tuple of (out_keystates, in_keystates)

    Example:
        out_ks, in_ks = crossfade(circle1, circle2, at=0.3, dur=0.2)
        elem_out = VElement().segment(out_ks)
        elem_in = VElement().segment(in_ks)
    """
    transition = TransitionConfig(easing=easing) if easing else None

    # Outgoing element: visible -> invisible
    s_out_visible = replace(s_out, opacity=s_out.opacity if hasattr(s_out, 'opacity') else 1.0)
    s_out_gone = replace(s_out, opacity=0.0)

    out_keystates = [
        KeyState(state=s_out_visible, time=at, transition_config=transition),
        KeyState(state=s_out_gone, time=min(1, at + dur)),
    ]

    # Incoming element: invisible -> visible
    s_in_gone = replace(s_in, opacity=0.0)
    s_in_visible = replace(s_in, opacity=s_in.opacity if hasattr(s_in, 'opacity') else 1.0)

    in_keystates = [
        KeyState(state=s_in_gone, time=at, transition_config=transition),
        KeyState(state=s_in_visible, time=min(1, at + dur)),
    ]

    return out_keystates, in_keystates
