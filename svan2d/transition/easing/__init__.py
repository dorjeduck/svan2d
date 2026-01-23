"""Easing functions for animation timing control.

Easing functions map linear time (0.0-1.0) to eased time, controlling
the rate of change during animations. All functions follow the signature:

    def easing(t: float) -> float

Available functions:
- linear, step, none: Basic functions
- in_*, out_*, in_out_*: Directional variants for each curve type
- Curve types: quad, cubic, quart, quint, sine, expo, circ, back, elastic, bounce
- easing2D: Create 2D easing with independent x/y control
"""

from typing import Callable, Tuple

from .in_back import in_back
from .in_bounce import in_bounce
from .in_circ import in_circ
from .in_cubic import in_cubic
from .in_elastic import in_elastic
from .in_expo import in_expo
from .in_out import in_out
from .in_out_back import in_out_back
from .in_out_bounce import in_out_bounce
from .in_out_circ import in_out_circ
from .in_out_cubic import in_out_cubic
from .in_out_elastic import in_out_elastic
from .in_out_expo import in_out_expo
from .in_out_quad import in_out_quad
from .in_out_quart import in_out_quart
from .in_out_quint import in_out_quint
from .in_out_sine import in_out_sine
from .in_quad import in_quad
from .in_quart import in_quart
from .in_quint import in_quint
from .in_sine import in_sine
from .linear import linear

# Individual easing functions
from .none import none
from .out_back import out_back
from .out_bounce import out_bounce
from .out_circ import out_circ
from .out_cubic import out_cubic
from .out_elastic import out_elastic
from .out_expo import out_expo
from .out_quad import out_quad
from .out_quart import out_quart
from .out_quint import out_quint
from .out_sine import out_sine
from .step import step


def easing2D(
    easing_x: Callable[[float], float],
    easing_y: Callable[[float], float],
) -> Callable[[float], Tuple[float, float]]:
    """Create a 2D easing function with independent easing per dimension.

    Returns an easing function that applies different easing functions to x and y,
    enabling independent control over horizontal and vertical motion timing.

    Args:
        easing_x: Easing function for x dimension
        easing_y: Easing function for y dimension

    Returns:
        Callable that takes t (0.0-1.0) and returns (eased_tx, eased_ty)

    Example:
        from svan2d.transition.easing import in_quad, out_bounce, easing2D
        # Fast horizontal, bouncy vertical
        pos_easing = easing2D(in_quad, out_bounce)
        element = VElement(
        ...     keystates=[...],
        ...     attribute_easing={"pos": pos_easing}
        ... )
    """

    def combined(t: float) -> Tuple[float, float]:
        return (easing_x(t), easing_y(t))

    return combined


__all__ = [
    "none",
    "step",
    "linear",
    "in_out",
    "out_cubic",
    "in_cubic",
    "in_out_cubic",
    "in_quad",
    "out_quad",
    "in_out_quad",
    "in_quart",
    "out_quart",
    "in_out_quart",
    "in_quint",
    "out_quint",
    "in_out_quint",
    "in_sine",
    "out_sine",
    "in_out_sine",
    "in_expo",
    "out_expo",
    "in_out_expo",
    "in_circ",
    "out_circ",
    "in_out_circ",
    "in_back",
    "out_back",
    "in_out_back",
    "in_elastic",
    "out_elastic",
    "in_out_elastic",
    "in_bounce",
    "out_bounce",
    "in_out_bounce",
    "easing2D",
]
