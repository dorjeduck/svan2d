"""State for collections of states that morph M→N"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from svan2d.component.registry import renderer
from svan2d.component.state.base import State


# Forward reference - actual import happens in renderer module
def _get_renderer():
    from svan2d.component.renderer.state_collection import StateCollectionRenderer

    return StateCollectionRenderer


@renderer(_get_renderer)
@dataclass(frozen=True)
class StateCollectionState(State):
    """State containing a collection of  that can morph M→N

    This enables general M→N state morphing where multiple independent
    states can smoothly transition to a different number of states.

    Example:
        # 3 states → 2 states morphing
        state1 = ShapeCollectionState(states=[
            CircleState(x=-50, radius=30),
            RectangleState(x=0, width=40, height=40),
            CircleState(x=50, radius=30)
        ])
        state2 = ShapeCollectionState(states=[
            EllipseState(x=-40, rx=50, ry=30),
            EllipseState(x=40, rx=50, ry=30)
        ])

        elem = VElement(keystates=[state1, state2])
    """

    states: List[State] | None = None
