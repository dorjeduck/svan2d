"""Fade in/out segment function."""

from dataclasses import replace
from typing import List, Optional, Union

from svan2d.velement.keystate import KeyState
from svan2d.component.state.base import State
from .utils import linspace


def fade_inout(
    states: Union[State, List[State]],
    at: Optional[Union[float, List[float]]] = None,
    hold_duration: Optional[float] = None,
    fade_duration: Optional[float] = None,
) -> List[KeyState]:
    """Fade in, hold, then fade out.

    Args:
        states: State to fade, or list of states
        at: Center time of the hold, or list of times
        hold_duration: Duration of the hold period
        fade_duration: Duration of each fade (in and out)

    Returns:
        List of KeyState objects
    """

    def get_keystates(state, t, hold_dur, fade_dur):
        half_hold = hold_dur / 2
        sgone = replace(state, opacity=0)

        res = []

        if t - half_hold > 0:
            res.append(KeyState(state=sgone, time=max(0, t - half_hold - fade_dur)))
        res.append(KeyState(state=state, time=max(0, t - half_hold)))
        res.append(KeyState(state=state, time=min(1, t + half_hold)))
        if t + half_hold < 1:
            res.append(KeyState(state=sgone, time=min(1, t + half_hold + fade_dur)))

        return res

    # Handle single state case
    if isinstance(states, State):
        if at is None:
            at = 0.5
        if hold_duration is None:
            hold_duration = 1.0 / 3
        if fade_duration is None:
            fade_duration = 1.0 / 9

        if isinstance(at, list):
            raise ValueError("'at' must be float when 'states' is a single State")

        return get_keystates(states, at, hold_duration, fade_duration)

    # Handle list of states
    if at is None:
        at = linspace(len(states))
    if hold_duration is None:
        hold_duration = 1.0 / (3 * len(states))
    if fade_duration is None:
        fade_duration = 1.0 / (9 * len(states))

    if not isinstance(at, list):
        raise ValueError("'at' must be a list when 'states' is a list of States")
    if len(states) != len(at):
        raise ValueError(
            f"Length of 'states' ({len(states)}) must match length of 'at' ({len(at)})"
        )

    result = []
    for s, t in zip(states, at):
        result.extend(get_keystates(s, t, hold_duration, fade_duration))

    return result
