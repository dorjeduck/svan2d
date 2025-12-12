"""Fade animation - crossfade between N states"""

from dataclasses import replace
from typing import List, Optional

from svan2d.component import State
from svan2d.velement import VElement


def fade(
    states: List[State],
    start: float = 0.0,
    end: float = 1.0,
    fade_duration: float = 0.1,
    gap: float = 0.0,
    builder: Optional[VElement] = None,
) -> List[VElement]:
    """Create fade transitions between N states.

    Each state fades out while the next fades in. Returns independent
    VElements, each handling one state's lifecycle.

    Args:
        states: List of states to transition between (minimum 2)
        start: Start time of first state (0.0-1.0)
        end: End time of last state (0.0-1.0)
        fade_duration: Duration of each fade out/in
        gap: Time gap between fade-out end and fade-in start.
             Positive = pause between states
             Negative = overlap (crossfade effect)
             Zero = seamless handoff
        builder: Optional VElement to continue from. If provided,
                 it is used for the first state instead of creating a new
                 element. This allows chaining animations.

    Returns:
        List of VElements. The last element can have additional keystates
        added for continuation (before first render).

    Example:
        # Simple fade through 3 states
        elements = fade([s1, s2, s3])
        scene.add_elements(elements)

        # Crossfade with overlap
        elements = fade([s1, s2], gap=-0.05)

        # Continue after fade
        elements = fade([s1, s2], end=0.5)
        elements[-1].keystate(s3, at=1.0)  # Add continuation
        scene.add_elements(elements)

        # Chain from existing element
        elem = VElement().keystate(s1, at=0.0).keystate(s2, at=0.3)
        elements = fade([s2, s3, s4], start=0.3, end=1.0, builder=elem)
    """
    if len(states) < 2:
        raise ValueError("fade requires at least 2 states")

    n = len(states)
    total_duration = end - start

    # Calculate timing for each transition
    # With N states, we have N-1 transitions
    # Each transition needs: fade_out + gap + fade_in
    transition_duration = fade_duration + gap + fade_duration
    num_transitions = n - 1

    # Time available for "holding" states between transitions
    total_transition_time = transition_duration * num_transitions
    total_hold_time = total_duration - total_transition_time

    if total_hold_time < 0:
        raise ValueError(
            f"Not enough time for {num_transitions} transitions. "
            f"Need {total_transition_time:.3f}, have {total_duration:.3f}"
        )

    # Distribute hold time evenly across states
    hold_per_state = total_hold_time / n

    elements: List[VElement] = []
    current_time = start

    for i, state in enumerate(states):
        is_first = i == 0
        is_last = i == n - 1

        # Calculate this element's timeline
        if is_first:
            # First element: starts visible, fades out at end
            elem_start = current_time
            elem_end = current_time + hold_per_state + fade_duration
            start_opacity = 1.0
            end_opacity = 0.0
        elif is_last:
            # Last element: fades in, stays visible
            elem_start = current_time
            elem_end = end
            start_opacity = 0.0
            end_opacity = 1.0
        else:
            # Middle elements: fade in, hold, fade out
            elem_start = current_time
            elem_end = current_time + fade_duration + hold_per_state + fade_duration
            start_opacity = 0.0
            end_opacity = 0.0

        # Build the element - use provided builder for first state, else create new
        if is_first and builder is not None:
            elem = builder
        else:
            elem = VElement()

        if is_first:
            # Visible at start, fade out
            elem.keystate(replace(state, opacity=start_opacity), at=elem_start)
            elem.keystate(replace(state, opacity=end_opacity), at=elem_end)
        elif is_last:
            # Fade in, visible at end
            fade_in_end = elem_start + fade_duration
            elem.keystate(replace(state, opacity=start_opacity), at=elem_start)
            elem.keystate(replace(state, opacity=1.0), at=fade_in_end)
            if fade_in_end < elem_end:
                elem.keystate(replace(state, opacity=1.0), at=elem_end)
        else:
            # Middle: fade in, hold, fade out
            fade_in_end = elem_start + fade_duration
            fade_out_start = elem_end - fade_duration
            elem.keystate(replace(state, opacity=0.0), at=elem_start)
            elem.keystate(replace(state, opacity=1.0), at=fade_in_end)
            if fade_in_end < fade_out_start:
                elem.keystate(replace(state, opacity=1.0), at=fade_out_start)
            elem.keystate(replace(state, opacity=0.0), at=elem_end)

        elements.append(elem)

        # Advance time for next element
        if not is_last:
            # Next element starts after: hold + fade_out + gap
            if is_first:
                current_time = elem_end + gap
            else:
                current_time = elem_end - fade_duration + gap

    return elements
