from dataclasses import replace
from typing import Callable, Dict, List, Optional, Union

from svan2d.core.point2d import Point2D
from svan2d import transition
from svan2d.transition.segment.slide_hold_slide import SlideEffect
from svan2d.velement.keystate import KeyState, KeyStates
from svan2d.component.state.base import State
from svan2d.velement.transition import TransitionConfig
from .utils import linspace


def just_slide(
    states: Union[State, List[State]],
    *,
    t_start: float,
    t_end: float,
    entrance_point: Point2D = Point2D(50.0, 0.0),
    exit_point: Point2D = Point2D(-50.0, 0.0),
    entrance_effect: SlideEffect = SlideEffect.NONE,
    exit_effect: SlideEffect = SlideEffect.NONE,
    entrance_easing_dict: Optional[Dict[str, Callable[[float], float]]] = None,
    exit_easing_dict: Optional[Dict[str, Callable[[float], float]]] = None,
) -> Union[List[KeyState], List[List[KeyState]]]:

    num_states = 1 if isinstance(states, State) else len(states)
    slide_duration = (t_end - t_start) / (num_states + 1)

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

    def get_transition_config(easing_dict):
        if easing_dict:
            if not "pos" in easing_dict:
                easing_dict["pos"] = transition.easing.linear
        else:
            easing_dict = {"pos": transition.easing.linear}

        return TransitionConfig(easing_dict=easing_dict)

    def make_keystates(
        state: State, t: float, entrance_easing_dict, exit_easing_dict
    ) -> List[KeyState]:

        entrance_transition_config = get_transition_config(entrance_easing_dict)
        exit_transition_config = get_transition_config(exit_easing_dict)

        res: KeyStates = []

        slide_start_in = t
        center = t + slide_duration
        slide_end_out = min(t_end, center + slide_duration)  # rounding error clamp

        s_in = apply_effect(slid(state, entrance_point), entrance_effect)
        s_out = apply_effect(slid(state, exit_point), exit_effect)

        res.append(
            KeyState(
                state=s_in,
                time=slide_start_in,
                transition_config=entrance_transition_config,
            )
        )
        res.append(
            KeyState(
                state=state,
                time=center,
                transition_config=exit_transition_config,
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
        return make_keystates(states, t_start, entrance_easing_dict, exit_easing_dict)

    result: List[List[KeyState]] = []
    for i, s in enumerate(states):
        t = t_start + i * slide_duration

        result.append(make_keystates(s, t, entrance_easing_dict, exit_easing_dict))

    return result
