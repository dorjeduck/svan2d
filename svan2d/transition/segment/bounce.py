"""Bounce segment function."""

from typing import List, Optional, Callable, Dict

from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig
from svan2d.component.state.base import State


def bounce(
    s1: State,
    s2: State,
    t_start: float,
    t_end: float,
    hold_duration: Optional[float] = 0,
    num_transitions: int = 2,
    easing: Optional[Dict[str, Callable[[float], float]]] = None,
) -> List[KeyState]:
    """Bounce between two states.

    Args:
        s1: First state (start and end)
        s2: Second state (peaks)
        t_start: Start time
        t_end: End time
        hold_duration: Optional[float]: how long to hold the state in the in between stages
        num_transitions: Number of transitions
            (3 = s1->s2->s1->s2)
            (4 = s1->s2->s1->s2->s1)
        easing: Optional easing dict for transitions

    Returns:
        List of KeyState objects

    """
    result = []
    dur = t_end - t_start
    hold_total = (num_transitions - 1) * hold_duration
    step = (dur - hold_total) / num_transitions
    transition = TransitionConfig(easing_dict=easing) if easing else None

    if step <= 0:
        raise ValueError(
            "bounce: sum of hold durations must be smaller than total duration "
        )

    for i in range(num_transitions + 1):
        state = s1 if i % 2 == 0 else s2

        if i == 0:
            result.append(
                KeyState(
                    state=state,
                    time=t_start,
                    transition_config=transition,
                )
            )
        elif i == num_transitions:
            result.append(
                KeyState(
                    state=state,
                    time=t_end,
                )
            )
        else:
            next_t = t_start + i * step + (i - 1) * hold_duration

            if hold_duration > 0:
                result.append(KeyState(state=state, time=next_t))

            result.append(
                KeyState(
                    state=state,
                    time=next_t + hold_duration,
                    transition_config=transition,
                )
            )

    return result
