# ============================================================================
# svan2D/animations/atomic/slide.py
# ============================================================================
"""Slide out, switch, slide in animation"""

from typing import Union
from dataclasses import replace
from svan2d.component import State
from svan2d.core.point2d import Point2D
from ..enums import SlideDirection
from svan2d.velement.keystate import KeyState, KeyStates


def slide(
    state1: State,
    state2: State,
    at_time: float = 0.5,
    duration: float = 0.3,
    direction: Union[SlideDirection, str] = SlideDirection.LEFT,
    distance: float = 100,
    extend_timeline: bool = False,
) -> KeyStates:
    """Slide out first state, switch attributes, slide in second state

    Element slides off-screen in one direction, attributes change, then
    slides back in from the opposite direction.

    Args:
        state1: Starting state (will slide out)
        state2: Ending state (will slide in)
        at_time: Center point of the transition (0.0 to 1.0)
        duration: Total duration of slide out + slide in (0.0 to 1.0)
        direction: Direction to slide out (SlideDirection enum or string)
        distance: Distance to slide in pixels
        extend_timeline: If True, adds keystates at 0.0 and 1.0 to cover full timeline

    Returns:
        List of keystates for single element

    Example:
        >>> from svan2D.animations.atomic import slide, SlideDirection
        >>>
        >>> # Element only exists during slide (partial timeline)
        >>> keystates = slide(
        ...     TextState(text="Before", pos=Point2D(100, 0)),
        ...     TextState(text="After", pos=Point2D(100, 0)),
        ...     direction=SlideDirection.LEFT,
        ...     distance=200
        ... )
        >>> element = VElement(renderer, keystates=keystates)
    """
    # Convert string to enum if needed
    if isinstance(direction, str):
        direction = SlideDirection(direction)

    half = duration / 2
    t_start = at_time - half
    t_end = at_time + half

    # Determine which field to animate and offsets
    direction_config = {
        SlideDirection.LEFT: (Point2D(-distance, 0), Point2D(distance, 0)),
        SlideDirection.RIGHT: (Point2D(distance, 0), Point2D(-distance, 0)),
        SlideDirection.UP: (Point2D(0, distance), Point2D(0, -distance)),
        SlideDirection.DOWN: (Point2D(0, -distance), Point2D(0, distance)),
    }

    out_offset, in_offset = direction_config[direction]

    # Get original positions
    orig_pos_1 = getattr(state1, "pos")
    orig_pos_2 = getattr(state2, "pos")

    keystates = [
        KeyState(time=t_start, state=state1),
        KeyState(
            time=at_time,
            state=replace(state1, **{"pos": orig_pos_1 + out_offset}, opacity=0.0),
        ),  # Slid out
        KeyState(
            time=at_time,
            state=replace(state2, **{"pos": orig_pos_2 + in_offset}, opacity=0.0),
        ),  # Switch (off-screen)
        KeyState(
            time=t_end, state=replace(state2, **{"pos": orig_pos_2}, opacity=1.0)
        ),  # Slid in
    ]

    if extend_timeline:
        keystates = [
            KeyState(time=0.0, state=state1),
            *keystates,
            KeyState(time=1.0, state=state2),
        ]

    return keystates
