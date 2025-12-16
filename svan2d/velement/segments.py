"""Segment functions for timeline patterns.

Segment functions are reusable timeline generators that expand into
sequences of KeyState objects. Use with VElement.segment():

    from svan2d.velement.segments import hold

    element = (
        VElement()
        .keystate(s1, at=0.0)
        .segment(hold(s2, at=0.3, dur=0.1))
        .keystate(s3, at=1.0)
    )
"""

from dataclasses import replace
from typing import List, Optional, Callable, Dict, Union, Tuple

from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig
from svan2d.component.state.base import State


def linspace(n):
    if n == 1:
        return [0.0]
    return [i / (n - 1) for i in range(n)]


def hold(
    states: Union[State, List[State]],
    at: Optional[Union[float, List[float]]] = None,
    duration: Optional[float] = None,
) -> List[KeyState]:
    """Hold at state(s) for a duration, centered at 'at'.

    Creates two identical keystates bracketing each hold period.

    Args:
        state: State to hold, or list of states
        at: Center time of the hold, or list of times (same length as states)
        dur: Total duration of each hold

    Returns:
        List of KeyState objects

    Example:
        # Single state hold
        .segment(hold(s, at=0.5, dur=0.1))
        # Expands to keystates at t=0.45 and t=0.55

        # Multiple states with different times
        .segment(hold([s1, s2, s3], at=[0.2, 0.5, 0.8], dur=0.1))
        # Expands to 6 keystates (2 per state)
    """
    half = duration / 2

    # Handle single state case
    if isinstance(states, State):
        if at == None:
            at = 0.5
        if duration == None:
            duration = 1.0 / 3
        if isinstance(at, list):
            raise ValueError("'at' must be float when 'state' is a single State")

        return [
            KeyState(state=states, time=max(0, at - half)),
            KeyState(state=states, time=min(1, at + half)),
        ]

    if at == None:
        at = linspace(len(states))
    if duration == None:
        duration = 1.0 / (3 * len(states))

    if not isinstance(at, list):
        raise ValueError("'at' must be a list when 'states' is a list of States")
    if len(states) != len(at):
        raise ValueError(
            f"Length of 'states' ({len(states)}) must match length of 'at' ({len(at)})"
        )

    result = []
    for s, t in zip(states, at):
        result.append(KeyState(state=s, time=max(0, t - half)))
        result.append(KeyState(state=s, time=min(1, t + half)))

    return result


def fade_inout(
    states: Union[State, List[State]],
    at: Optional[Union[float, List[float]]] = None,
    hold_duration: Optional[float] = None,
    fade_duration: Optional[float] = None,
) -> List[KeyState]:

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

        if at == None:
            at = 0.5
        if hold_duration == None:
            hold_duration = 1.0 / 3
        if fade_duration == None:
            fade_duration = 1.0 / 9

        if isinstance(at, list):
            raise ValueError("'at' must be float when 'state' is a single State")

        return get_keystates(states, at, hold_duration, fade_duration)

    if at == None:
        at = linspace(len(states))
    if hold_duration == None:
        hold_duration = 1.0 / (3 * linspace(states))
    if fade_duration == None:
        fade_duration = 1.0 / (9 * linspace(states))

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
    transition = TransitionConfig(easing_dict=easing) if easing else None

    for i in range(times * 2 + 1):
        state = s1 if i % 2 == 0 else s2
        # Last keystate has no outgoing transition
        tc = transition if i < times * 2 else None
        result.append(KeyState(state=state, time=at + i * step, transition_config=tc))

    return result


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
    transition = TransitionConfig(easing_dict=easing) if easing else None

    # Outgoing element: visible -> invisible
    s_out_visible = replace(
        s_out, opacity=s_out.opacity if hasattr(s_out, "opacity") else 1.0
    )
    s_out_gone = replace(s_out, opacity=0.0)

    out_keystates = [
        KeyState(state=s_out_visible, time=at, transition_config=transition),
        KeyState(state=s_out_gone, time=min(1, at + dur)),
    ]

    # Incoming element: invisible -> visible
    s_in_gone = replace(s_in, opacity=0.0)
    s_in_visible = replace(
        s_in, opacity=s_in.opacity if hasattr(s_in, "opacity") else 1.0
    )

    in_keystates = [
        KeyState(state=s_in_gone, time=at, transition_config=transition),
        KeyState(state=s_in_visible, time=min(1, at + dur)),
    ]

    return out_keystates, in_keystates
