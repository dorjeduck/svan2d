"""Slide out segment function (single-element)."""

from dataclasses import replace, dataclass
from typing import List, Optional, Callable, Dict, Tuple, Union

from svan2d.core.point2d import Point2D
from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig
from svan2d.component.state.base import State  # Assuming State is imported


# -------------------------------------------------------------------------------------

# Redefine PositionOffset to be consistent with the coordinate type
PositionOffset = Tuple[Union[float, int], Union[float, int]]


def slide_out(
    s_start: State,
    to_offset: PositionOffset,
    at: float,
    dur: float,
    easing: Optional[Dict[str, Callable[[float], float]]] = None,
) -> List[KeyState]:
    """Slide an element out of its starting position towards an offset, using the 'pos: Point2D' attribute.

    Args:
        s_start: The State representing the element's starting position and appearance.
                 This state must have a 'pos' attribute of type Point2D.
        to_offset: A tuple (dx, dy) representing the distance from the
                   starting position where the element ends.
        at: Start time of the slide out.
        dur: Duration of the slide out.
        easing: Optional easing dict for position transitions.

    Returns:
        List of keystates (out_keystates)
    """
    transition = TransitionConfig(easing=easing) if easing else None

    # 1. Access the starting position from the State's 'pos' attribute
    pos_start: Point2D = getattr(s_start, "pos")

    # 2. Determine the final position (offset from start)
    dx, dy = to_offset
    x_final = pos_start.x + dx
    y_final = pos_start.y + dy

    # 3. Create the final Point2D object
    pos_final = Point2D(x=x_final, y=y_final)

    # 4. Create the ending State by replacing the 'pos' attribute
    s_final = replace(s_start, pos=pos_final)

    # 5. Create the Keystates
    out_keystates = [
        # Start at the on-screen position
        KeyState(state=s_start, time=at - dur / 2, transition_config=transition),
        # End at the off-screen position
        KeyState(state=s_final, time=min(1, at + dur / 2)),
    ]

    return out_keystates
