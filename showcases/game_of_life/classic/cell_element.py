"""Cell element creation with animation based on life history."""

from dataclasses import replace
from typing import List

from svan2d.component.state import SquareState
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement import VElement

from config import (
    BIRTH_DURATION,
    CELL_GAP,
    CELL_SIZE,
    COLOR_ALIVE,
    COLOR_DEATH,
    DEATH_DURATION,
    GENERATIONS,
)


def create_cell_element(
    grid_x: int,
    grid_y: int,
    life_history: List[bool],
    grid_size: int,
) -> VElement | None:
    """Create animated cell VElement based on its life history.

    Both birth and death animate scale and opacity.
    Separate durations allow for quick births and slow fade-out traces.
    """
    if not any(life_history):
        return None

    # Calculate pixel position (centered grid)
    cell_spacing = CELL_SIZE + CELL_GAP
    grid_width = grid_size * cell_spacing
    offset = -grid_width / 2 + cell_spacing / 2

    pos = Point2D(
        offset + grid_x * cell_spacing,
        offset + grid_y * cell_spacing,
    )

    # Base states (both scale and opacity differ)
    alive_state = SquareState(
        size=CELL_SIZE,
        pos=pos,
        fill_color=COLOR_ALIVE,
        scale=1.0,
        opacity=1.0,
        corner_radius=2,
    )
    dead_state = replace(
        alive_state,
        scale=0.0,
        opacity=0.0,
        fill_color=COLOR_DEATH,
    )

    # Time calculations
    gen_duration = 1.0 / GENERATIONS
    birth_time = gen_duration * BIRTH_DURATION
    death_time = gen_duration * DEATH_DURATION

    # Collect state change events: (generation, becomes_alive)
    events = [(0, life_history[0])]
    for gen in range(1, len(life_history)):
        if life_history[gen] != life_history[gen - 1]:
            events.append((gen, life_history[gen]))

    # Build keystates
    element = VElement()

    for i, (gen, becomes_alive) in enumerate(events):
        t_change = gen * gen_duration
        trans_time = birth_time if becomes_alive else death_time
        t_end = min(t_change + trans_time, 1.0)

        # Check if next event interrupts this transition
        next_event_time = None
        if i + 1 < len(events):
            next_event_time = events[i + 1][0] * gen_duration

        if gen == 0:
            # Initial state
            state = alive_state if becomes_alive else dead_state
            element = element.keystate(state, at=0.0)
        else:
            # State change: add "hold" keystate at change time
            prev_alive = not becomes_alive
            hold_state = alive_state if prev_alive else dead_state
            element = element.keystate(hold_state, at=t_change)

            # Set up transition easing
            if becomes_alive:
                element = element.transition(
                    easing_dict={"scale": easing.out_cubic, "opacity": easing.out_cubic}
                )
            else:
                element = element.transition(
                    easing_dict={"scale": easing.in_cubic, "opacity": easing.in_cubic}
                )

            # Only add end keystate if not interrupted by next event
            if next_event_time is None or next_event_time >= t_end:
                target_state = alive_state if becomes_alive else dead_state
                element = element.keystate(target_state, at=t_end)

    # Ensure final keystate at t=1.0
    final_alive = life_history[-1]
    final_state = alive_state if final_alive else dead_state

    last_gen = events[-1][0]
    last_becomes_alive = events[-1][1]
    last_trans_time = birth_time if last_becomes_alive else death_time
    last_t_end = min(last_gen * gen_duration + last_trans_time, 1.0)

    if last_t_end < 1.0:
        element = element.keystate(final_state, at=1.0)

    return element
