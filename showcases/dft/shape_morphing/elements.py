"""VElement construction for the shape morphing showcase.

Morphs between shapes using svan2d's PathState morphing system.
Each shape is evaluated once from its Fourier coefficients to produce
SVG path data. svan2d's path morphing handles the interpolation.

Demonstrates svan2d animation features:
- Path morphing: automatic interpolation between SVG paths
- Keystate chaining: .keystate().transition().keystate() pattern
- Easing: smooth morph timing via easing functions
"""

from __future__ import annotations

from svan2d.component.state.path import MorphMethod, PathState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement import VElement

from fourier import FourierCoefficient, evaluate_shape_loop


def _vertices_to_path_string(vertices: list[complex]) -> str:
    """Convert complex vertices to SVG path string."""
    if not vertices:
        return ""

    parts = [f"M {vertices[0].real:.2f},{vertices[0].imag:.2f}"]
    for v in vertices[1:]:
        parts.append(f"L {v.real:.2f},{v.imag:.2f}")
    parts.append("Z")
    return " ".join(parts)


def create_morphing_elements(
    shape_coefficients: list[list[FourierCoefficient]],
    trail_color: Color,
    trail_width: float,
) -> list[VElement]:
    """Build VElements for the shape morphing animation.

    Creates one VElement with N+1 keystates (one per shape + return to first).
    svan2d handles path morphing between shapes automatically.

    Args:
        shape_coefficients: List of coefficient sets, one per shape.

    Returns:
        List with one VElement using path morphing.
    """
    num_shapes = len(shape_coefficients)
    num_transitions = num_shapes  # includes return to first shape
    num_loop_vertices = 200

    # Evaluate each shape's path once
    shape_states: list[PathState] = []
    for coeffs in shape_coefficients:
        loop = evaluate_shape_loop(coeffs, num_loop_vertices)
        path_string = _vertices_to_path_string(loop)

        state = PathState(
            pos=Point2D(0, 0),
            data=path_string,
            stroke_color=trail_color,
            stroke_width=trail_width,
            fill_color=Color.NONE,
            morph_method=MorphMethod.STROKE,
            z_index=1.0,
        )
        shape_states.append(state)

    # Build keystate chain: shape0 → shape1 → ... → shapeN → shape0
    element = VElement()

    for i in range(num_transitions):
        t = i / num_transitions
        element = element.keystate(shape_states[i % num_shapes], at=t)
        element = element.transition(
            easing_dict={"data": easing.in_out_cubic}
        )

    # Return to first shape at t=1.0
    element = element.keystate(shape_states[0], at=1.0)

    return [element]
