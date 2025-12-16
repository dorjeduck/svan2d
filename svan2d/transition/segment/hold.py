"""Hold segment function."""

from typing import Callable, Dict, List, Optional, Union

from svan2d.velement.keystate import KeyState
from svan2d.component.state.base import State
from svan2d.velement.transition import TransitionConfig
from .utils import linspace


def hold(
    states: Union[State, List[State]],
    t_start: float,
    t_end: float,
    hold_duration: Optional[float] = None,
    easing: Optional[Dict[str, Callable[[float], float]]] = None,
) -> List[KeyState]:
    """Hold at state(s) for a duration, centered at 'at'.

    Creates two identical keystates bracketing each hold period.

    Args:
        states: State to hold, or list of states
        at: Center time of the hold, or list of times (same length as states)
        duration: Total duration of each hold

    Returns:
        List of KeyState objects

    Example:
        # Single state hold
        .segment(hold(s, at=0.5, duration=0.1))
        # Expands to keystates at t=0.45 and t=0.55

        # Multiple states with different times
        .segment(hold([s1, s2, s3], at=[0.2, 0.5, 0.8], duration=0.1))
        # Expands to 6 keystates (2 per state)
    """
    # Handle single state case
    if isinstance(states, State):
        if at is None:
            at = 0.5
        if hold_duration is None:
            hold_duration = 1.0 / 3
        if isinstance(at, list):
            raise ValueError("'at' must be float when 'states' is a single State")

        half = hold_duration / 2
        return [
            KeyState(state=states, time=max(0, at - half)),
            KeyState(state=states, time=min(1, at + half)),
        ]

    transition = TransitionConfig(easing_dict=easing) if easing else None

    # Handle list of states
    if at is None:
        at = linspace(len(states))
    if hold_duration is None:
        hold_duration = 1.0 / (3 * len(states))

    half = hold_duration / 2

    if not isinstance(at, list):
        raise ValueError("'at' must be a list when 'states' is a list of States")
    if len(states) != len(at):
        raise ValueError(
            f"Length of 'states' ({len(states)}) must match length of 'at' ({len(at)})"
        )

    result = []
    n = len(states)

    for i, (s, t) in enumerate(zip(states, at)):
        result.append(KeyState(state=s, time=max(0, t - half)))

        is_last = i == n - 1

        if not (is_last and transition is None):
            result.append(
                KeyState(
                    state=s,
                    time=min(
                        1,
                        t + half,
                    ),
                    transition_config=transition,
                )
            )
        else:
            result.append(
                KeyState(
                    state=s,
                    time=min(
                        1,
                        t + half,
                    ),
                )
            )

    return result
