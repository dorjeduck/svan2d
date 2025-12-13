"""Segment functions for timeline patterns.

Segment functions are reusable timeline generators that expand into
sequences of KeyState objects. Use with VElement.segment():

    from svan2d.velement.segment import hold

    element = (
        VElement()
        .keystate(s1, at=0.0)
        .segment(hold(s2, at=0.3, dur=0.1))
        .keystate(s3, at=1.0)
    )

Multi-element segment functions return tuples:

    from svan2d.velement.segment import crossfade

    out_ks, in_ks = crossfade(s1, s2, at=0.3, dur=0.2)
    elem_out = VElement().segment(out_ks)
    elem_in = VElement().segment(in_ks)
"""

from .utils import linspace
from .hold import hold
from .fade_inout import fade_inout
from .bounce import bounce
from .crossfade import crossfade

__all__ = [
    "linspace",
    "hold",
    "fade_inout",
    "bounce",
    "crossfade",
]
