from dataclasses import replace

from typing import Callable, Dict, List, Optional, Union

from svan2d.core.point2d import Point2D
from svan2d.transition.segment.slide_effect import SlideEffect
from svan2d.velement.keystate import KeyState, KeyStates
from svan2d.component.state.base import State
from svan2d.velement.transition import TransitionConfig
from .utils import linspace


def slide_hold_slide(
    states: Union[State, List[State]],
    *,
    t_start: float,
    t_end: float,
    slide_duration: float = 0.1,
    entrance_point: Point2D = Point2D(50.0, 0.0),
    exit_point: Point2D = Point2D(-50.0, 0.0),
    entrance_effect: SlideEffect = SlideEffect.NONE,
    exit_effect: SlideEffect = SlideEffect.NONE,
    entrance_easing_dict: Optional[Dict[str, Callable[[float], float]]] = None,
    exit_easing_dict: Optional[Dict[str, Callable[[float], float]]] = None,
) -> Union[List[KeyState], List[List[KeyState]]]:

    num_states = 1 if isinstance(states, State) else len(states)

    hold_duration = (t_end - t_start - (num_states + 1) * slide_duration) / num_states

    def apply_effect(state: State, effect: SlideEffect) -> State:
        if effect == SlideEffect.FADE:
            return replace(state, opacity=0)
        if effect == SlideEffect.SCALE:
            return replace(state, scale=0)
        if effect == SlideEffect.FADE_SCALE:
            return replace(state, opacity=0, scale=0)
        return state

    def slid(state: State, newpos: Point2D) -> State:
        return replace(state, pos=newpos)

    def make_keystates(state: State, t: float) -> List[KeyState]:
        entrance_transition = (
            TransitionConfig(easing_dict=entrance_easing_dict)
            if entrance_easing_dict
            else None
        )
        exit_transition = (
            TransitionConfig(easing_dict=exit_easing_dict) if exit_easing_dict else None
        )
        res: KeyStates = []

        slide_start_in = t
        hold_start = t + slide_duration
        hold_end = hold_start + hold_duration
        slide_end_out = min(t_end, hold_end + slide_duration)  # rounding error clamp

        s_in = apply_effect(slid(state, entrance_point), entrance_effect)
        s_out = apply_effect(slid(state, exit_point), exit_effect)

        res.append(
            KeyState(
                state=s_in,
                time=slide_start_in,
                transition_config=entrance_transition,
            )
        )
        res.append(
            KeyState(
                state=state,
                time=hold_start,
            )
        )
        res.append(
            KeyState(
                state=state,
                time=hold_end,
                transition_config=exit_transition,
            )
        )
        res.append(
            KeyState(
                state=s_out,
                time=slide_end_out,
            )
        )

        return res

    # Single state
    if isinstance(states, State):
        return make_keystates(states, t_start)

    result: List[List[KeyState]] = []
    for i, s in enumerate(states):
        t = t_start + i * (slide_duration + hold_duration)

        result.append(make_keystates(s, t))

    return result
