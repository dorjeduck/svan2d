# ============================================================================
# svan2D/animations/compound/bounce_replace.py
# ============================================================================
"""Bounce replace with sequential bouncing"""

from typing import Tuple
from dataclasses import replace
from svan2d.component import State
from svan2d.core.point2d import Point2D
from svan2d.velement.keystate import KeyState, KeyStates


def bounce_replace(
    state1: State,
    state2: State,
    at_time: float = 0.5,
    duration: float = 0.4,
    bounce_height: float = -50,
    extend_timeline: bool = False,
) -> Tuple[KeyStates, KeyStates]:
    """Bounce out first element, bounce in second element

    First element bounces up and away, second element bounces in from above.
    Creates a playful, energetic transition. Works well with bounce or
    elastic easing.

    Args:
        state1: Starting state (bounces away)
        state2: Ending state (bounces in)
        at_time: Center point of the transition (0.0 to 1.0)
        duration: Duration of the bounce (0.0 to 1.0)
        bounce_height: How high to bounce (negative = up, positive = down)
        extend_timeline: If True, adds keystates at 0.0 and 1.0 to cover full timeline

    Returns:
        Tuple of (element1_keyframes, element2_keyframes)

    Example:
        >>> from svan2D.animations.compound import bounce_replace
        >>> from svan2D.transitions import easing
        >>> from svan2D import VElement, VElementGroup
        >>>
        >>> kf1, kf2 = bounce_replace(
        ...     TextState(text="Old", y=100),
        ...     TextState(text="New", y=100),
        ...     bounce_height=-100
        ... )
        >>>
        >>> elem1 = VElement(text_renderer, keystates=kf1,
        ...                  attribute_easing={"y": easing.bounce})
        >>> elem2 = VElement(text_renderer, keystates=kf2,
        ...                  attribute_easing={"y": easing.bounce})
        >>> group = VElementGroup(elements=[elem1, elem2])
    """
    half = duration / 2
    t_start = at_time - half
    t_mid = at_time
    t_end = at_time + half

    # Get original y positions
    orig_1 = getattr(state1, "pos", Point2D())
    orig_2 = getattr(state2, "pos", Point2D())

    # Element 1: Bounce up and away
    keyframes1 = [
        KeyState(
            time=t_start, state=replace(state1, pos=orig_1, opacity=1.0, scale=1.0)
        ),
        KeyState(
            time=t_mid,
            state=replace(
                state1,
                pos=orig_1.with_y(orig_1.y + bounce_height),
                opacity=0.0,
                scale=0.5,
            ),
        ),
    ]

    # Element 2: Bounce down and in
    keyframes2 = [
        KeyState(
            time=t_mid,
            state=replace(
                state2,
                pos=orig_2.with_y(orig_2.y + bounce_height),
                opacity=0.0,
                scale=0.5,
            ),
        ),
        KeyState(time=t_end, state=replace(state2, pos=orig_2, opacity=1.0, scale=1.0)),
    ]

    if extend_timeline:
        keyframes1 = [
            KeyState(
                time=0.0, state=replace(state1, pos=orig_1, opacity=1.0, scale=1.0)
            ),
            *keyframes1,
        ]
        keyframes2 = [
            *keyframes2,
            KeyState(
                time=1.0, state=replace(state2, pos=orig_2, opacity=1.0, scale=1.0)
            ),
        ]

    return keyframes1, keyframes2
