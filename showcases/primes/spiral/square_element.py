from dataclasses import replace

from svan2d.component.state import SquareState, TextState
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement import VElement

from config import COLOR_TEXT, FADE_DURATION, GAP, SQUARE_SIZE
from utils import get_color, get_spiral_position


def create_square_element(
    n: int,
    appear_time: float,
    do_text: bool,
    text_fade_out_start: float,
) -> tuple[VElement, VElement | None]:
    """Create animated square and text elements for position n."""
    grid_x, grid_y = get_spiral_position(n)
    cell_size = SQUARE_SIZE + GAP
    pos = Point2D(grid_x * cell_size, -grid_y * cell_size)

    fade_end = min(appear_time + FADE_DURATION, 1.0)

    fade_out_end = min(text_fade_out_start + FADE_DURATION, 1.0)

    square_state_0 = SquareState(
        size=SQUARE_SIZE, pos=pos, fill_color=get_color(n), scale=0
    )
    square_state_1 = replace(square_state_0, scale=1)

    # Square with appearance animation
    square = (
        VElement()
        .keystate(
            square_state_0 if n > 1 else square_state_1,
            at=appear_time,
        )
        .transition(
            easing_dict={"scale": easing.out_cubic},
        )
        .keystate(
            square_state_1,
            at=fade_end,
        )
        .keystate(
            square_state_1,
            at=1.0,
        )
    )

    # Text with appearance animation
    if do_text:
        text_state_0 = TextState(
            text=str(n),
            pos=pos,
            font_size=SQUARE_SIZE * 0.35,
            fill_color=COLOR_TEXT,
            scale=0,
        )

        text_state_1 = replace(text_state_0, scale=1)

        text = (
            VElement()
            .keystate(
                text_state_0 if n > 1 else text_state_1,
                at=appear_time,
            )
            .transition(
                easing_dict={"scale": easing.out_cubic},
            )
            .keystate(
                text_state_1,
                at=fade_end,
            )
        )

        if text_fade_out_start < 1:
            text.keystate(
                text_state_0,
                at=fade_out_end,
            )

    else:
        text = None

    return square, text
