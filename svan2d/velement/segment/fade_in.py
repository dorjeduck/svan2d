"""Fade in segment function (single-element)."""

from dataclasses import replace
from typing import List, Optional, Callable, Dict, Tuple

from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig
from svan2d.component.state.base import State


def fade_in(
    s_out: State,
    at: float,
    dur: float,
    easing: Optional[Dict[str, Callable[[float], float]]] = None,
) -> List[KeyState]:
    """Fade an element in (invisible to visible).

    Returns a list of keystates for a single VElement.

    Args:
        s_out: State of the element (will fade from opacity 0)
        at: Start time of the fade in
        dur: Duration of the fade in
        easing: Optional easing dict for opacity transitions

    Returns:
        List of keystates (in_keystates)

    Example:
        in_ks = fade_in(circle, at=0.3, dur=0.2)
        elem_in = VElement().segment(in_ks)
    """
    transition = TransitionConfig(easing=easing) if easing else None

    # Element: invisible -> visible
    # The starting state is the same as the target, but with opacity 0.0
    s_gone = replace(s_out, opacity=0.0)

    # Ensure the ending opacity is correctly set from the State or defaults to 1.0
    s_visible = replace(
        s_out, opacity=s_out.opacity if hasattr(s_out, "opacity") else 1.0
    )

    # Following the crossfade/fade_out structure (using a duration before and after 'at'):
    in_keystates = [
        # Start completely gone at `at - dur / 2`
        KeyState(state=s_gone, time=at - dur / 2, transition_config=transition),
        # End fully visible at `at + dur / 2`
        KeyState(state=s_visible, time=min(1, at + dur / 2)),
    ]

    return in_keystates
