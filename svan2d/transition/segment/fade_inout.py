"""Fade in/out segment function."""

from dataclasses import replace
from collections.abc import Callable

from svan2d.primitive.state.base import State
from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig

from . import linspace


def fade_inout(
    states: State | list[State],
    center_t: float | list[float] | None = None,
    hold_duration: float | None = None,
    fade_duration: float | None = None,
    easing: dict[str, Callable[[float], float]] | None = None,
) -> list[list[KeyState]]:
    """Fade in, hold, then fade out.

    Args:
        states: State to fade, or list of states.
        center_t: Center time of the hold, or list of times.
        hold_duration: Duration of the hold period.
        fade_duration: Duration of each fade (in and out).
        easing: Optional easing dict for transitions.
    """

    def get_keystates(state, t, hold_dur, fade_dur, easing):

        transition = TransitionConfig(easing_dict=easing) if easing else None

        half_hold = hold_dur / 2
        sgone = replace(state, opacity=0)

        res = []

        if t - half_hold > 0:
            res.append(
                KeyState(
                    state=sgone,
                    time=max(0, t - half_hold - fade_dur),
                    transition_config=transition,
                )
            )
        res.append(KeyState(state=state, time=max(0, t - half_hold)))
        if t + half_hold < 1:
            res.append(
                KeyState(
                    state=state,
                    time=min(1, t + half_hold),
                    transition_config=transition,
                )
            )
            res.append(KeyState(state=sgone, time=min(1, t + half_hold + fade_dur)))
        else:
            res.append(KeyState(state=state, time=min(1, t + half_hold)))
        return res

    if isinstance(states, State):
        states = [states]

    if center_t is None:
        center_t = linspace(len(states))
    elif isinstance(center_t, (int, float)):
        center_t = [center_t]

    if hold_duration is None:
        hold_duration = 1.0 / (3 * len(states))
    if fade_duration is None:
        fade_duration = 1.0 / (9 * len(states))

    if len(states) != len(center_t):
        raise ValueError(
            f"Length of 'states' ({len(states)}) must match length of 'center_t' ({len(center_t)})"
        )

    result = []
    for s, t in zip(states, center_t):
        result.append(get_keystates(s, t, hold_duration, fade_duration, easing))

    return result
