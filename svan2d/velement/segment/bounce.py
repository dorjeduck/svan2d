"""Bounce segment function."""

from typing import List, Optional, Callable, Dict

from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig
from svan2d.component.state.base import State


def bounce(
    s1: State,
    s2: State,
    at: float,
    dur: float,
    times: int = 2,
    easing: Optional[Dict[str, Callable[[float], float]]] = None,
) -> List[KeyState]:
    """Bounce between two states.

    Args:
        s1: First state (start and end)
        s2: Second state (peaks)
        at: Start time
        dur: Total duration
        times: Number of bounces (2 = s1->s2->s1->s2->s1)
        easing: Optional easing dict for transitions

    Returns:
        List of KeyState objects

    Example:
        # Bounce twice between s1 and s2 over 0.2 duration
        .segment(bounce(s1, s2, at=0.3, dur=0.2, times=2))
    """
    result = []
    step = dur / (times * 2)
    transition = TransitionConfig(easing=easing) if easing else None

    for i in range(times * 2 + 1):
        state = s1 if i % 2 == 0 else s2
        # Last keystate has no outgoing transition
        tc = transition if i < times * 2 else None
        result.append(KeyState(state=state, time=at + i * step, transition_config=tc))

    return result
