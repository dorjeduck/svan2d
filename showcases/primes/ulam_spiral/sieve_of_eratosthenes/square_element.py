from dataclasses import replace

from svan2d.component.state import SquareState
from svan2d.core.point2d import Point2D
from svan2d.velement import VElement

from sieve import NumberStatus
from utils import get_spiral_position

from config import (
    COLOR_COMPOSITE,
    COLOR_ONE,
    COLOR_CANDIDATE,
    COLOR_PRIME,
    COLOR_CURRENT_SIEVE_PRIME,
    GAP,
    SQUARE_SIZE,
)


def create_square_element(n, report, step_time):
    grid_x, grid_y = get_spiral_position(n)
    cell_size = SQUARE_SIZE + GAP

    pos = Point2D(grid_x * cell_size, -grid_y * cell_size)

    state_start = SquareState(
        size=SQUARE_SIZE,
        pos=pos,
        fill_color=COLOR_CANDIDATE if n > 1 else COLOR_ONE,
    )

    if n == 1:
        return VElement().keystates([state_start, state_start])

    state_end = replace(
        state_start,
        fill_color=(
            COLOR_COMPOSITE
            if report["status"] == NumberStatus.COMPOSITE
            else COLOR_PRIME
        ),
    )

    change_time = (report["identified_at_step"] - 1) * step_time

    square = VElement()
    last_time = 0

    if (
        report["status"] == NumberStatus.COMPOSITE
        or report["status"] == NumberStatus.PRIME
    ):
        # Simple case: state_start -> state_end
        square = square.keystate(state_start, at=0)
        if change_time > 0:
            square = square.keystate(state_start, change_time)
        last_time = change_time + step_time
        square = square.keystate(state_end, last_time)

    else:
        # Sieve prime case: involves intermediate state_sieve color
        state_sieve = replace(state_start, fill_color=COLOR_CURRENT_SIEVE_PRIME)

        if report["identified_at_step"] == report["sieve_prime_at_step"]:
            # n == 2 case: identified at step 1, sieve at step 1
            # At t=0: show start, then switch to sieve
            square = square.keystate([state_start, state_sieve], at=0)
            last_time = change_time + step_time
            square = square.keystate([state_sieve, state_end], at=last_time)

        else:

            # Other sieve primes: identified later, sieve even later
            sieve_time = (report["sieve_prime_at_step"] - 1) * step_time

            square = square.keystate(state_start, at=0)

            if change_time > 0:
                square = square.keystate(state_start, at=change_time)
            if change_time + step_time < sieve_time:
                square = square.keystate(state_end, at=change_time + step_time)

            square = square.keystate([state_end, state_sieve], at=sieve_time)
            last_time = min(1, sieve_time + step_time)
            square = square.keystate([state_sieve, state_end], at=last_time, render_index=1)

    # Only add final keystate if not already at t=1
    if last_time < 1:
        square = square.keystate(state_end, at=1)

    return square
