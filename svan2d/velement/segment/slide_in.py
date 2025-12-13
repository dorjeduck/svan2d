"""Slide in segment function (single-element)."""

from dataclasses import replace, dataclass
from typing import List, Optional, Callable, Dict, Tuple, Union

from svan2d.core.point2d import Point2D
from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig
from svan2d.component.state.base import State  # Assuming State is imported


# -------------------------------------------------------------------------------------

# Redefine PositionOffset to be consistent with the coordinate type
PositionOffset = Tuple[Union[float, int], Union[float, int]]


def slide_in(
    s_final: State,
    from_offset: PositionOffset,
    at: float,
    dur: float,
    easing: Optional[Dict[str, Callable[[float], float]]] = None,
) -> List[KeyState]:
    """Slide an element into its final position from an offset, using the 'pos: Point2D' attribute.

    Args:
        s_final: The State representing the element's final position and appearance.
                 This state must have a 'pos' attribute of type Point2D.
        from_offset: A tuple (dx, dy) representing the distance from the
                     final position where the element starts.
        at: Start time of the slide in.
        dur: Duration of the slide in.
        easing: Optional easing dict for position transitions.

    Returns:
        List of keystates (in_keystates)
    """
    transition = TransitionConfig(easing=easing) if easing else None

    # 1. Access the final position from the State's 'pos' attribute
    pos_final: Point2D = getattr(s_final, "pos")

    # 2. Determine the starting position (offset from final)
    dx, dy = from_offset
    x_start = pos_final.x + dx
    y_start = pos_final.y + dy

    # 3. Create the starting Point2D object
    pos_start = Point2D(x=x_start, y=y_start)

    # 4. Create the starting State by replacing the 'pos' attribute
    s_start = replace(s_final, pos=pos_start)

    # 5. Create the Keystates
    in_keystates = [
        # Start at the off-screen position
        KeyState(state=s_start, time=at - dur / 2, transition_config=transition),
        # End at the final position
        KeyState(state=s_final, time=min(1, at + dur / 2)),
    ]

    return in_keystates
