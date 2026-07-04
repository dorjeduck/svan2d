"""Spiral layout state function"""

import math
from dataclasses import replace
from collections.abc import Callable

from svan2d.primitive.state.base import States
from svan2d.core.point2d import Point2D

from .enums import ElementAlignment


def spiral(
    states: States,
    center: Point2D = Point2D(0, 0),
    start_radius: float = 20,
    radius_step: float = 20,
    start_angle: float = 0,
    angle_step: float = 30,
    alignment: ElementAlignment = ElementAlignment.PRESERVE,
    element_rotation_offset: float = 0,
    element_rotation_offset_fn: Callable[[float], float] | None = None,
    angles: list[float] | None = None,
) -> States:
    """
    Arrange states in a spiral formation (Archimedean spiral).

    Each element is placed at increasing radius and angle from the center.
    Preserves all other state attributes (color, scale, opacity, etc.) while only
    modifying x and y positions.

    Args:
        states: List of states to arrange
        center: Center point of the spiral
        start_radius: Initial radius from center for first element
        radius_step: Amount to increase radius for each subsequent element
        start_angle: Initial angle in degrees for first element
        angle_step: Amount to increase angle for each subsequent element (degrees)
        alignment: How to align each element relative to the spiral.
                  PRESERVE keeps original rotation, LAYOUT aligns tangent to spiral,
                  UPRIGHT starts from vertical position.
        element_rotation_offset: Additional rotation in degrees added to the alignment base.
        element_rotation_offset_fn: Function that takes position angle (degrees) and returns rotation offset.
                           If provided, this overrides element_rotation_offset parameter.
    """
    if not states:
        return []

    result = []
    for i, state in enumerate(states):
        radius = start_radius + i * radius_step
        angle = angles[i] if angles is not None else start_angle + i * angle_step
        angle_rad = math.radians(angle)

        # Cartesian coordinates: 0° = East, counter-clockwise positive
        x = center.x + radius * math.cos(angle_rad)
        y = center.y + radius * math.sin(angle_rad)

        additional_rotation = (
            element_rotation_offset_fn(angle)
            if element_rotation_offset_fn
            else element_rotation_offset
        )

        if alignment == ElementAlignment.PRESERVE:
            element_angle = state.rotation
        elif alignment == ElementAlignment.LAYOUT:
            # Bottom faces center: element_angle = position_angle - 90
            element_angle = angle - 90 + additional_rotation
        elif alignment == ElementAlignment.UPRIGHT:
            element_angle = additional_rotation
        else:
            element_angle = state.rotation

        new_state = replace(state, pos=Point2D(x, y), rotation=element_angle)
        result.append(new_state)

    return result


def spiral_between_radii(
    states: States,
    center: Point2D,
    start_radius: float = 50,
    end_radius: float = 200,
    rotation: float = 0,
    counter_clockwise: bool = True,
    alignment: ElementAlignment = ElementAlignment.PRESERVE,
    element_rotation_offset: float = 0,
    element_rotation_offset_fn: Callable[[float], float] | None = None,
) -> States:
    """
    Arrange states in a spiral from start radius to end radius.

    Alternative specification to spiral() for users who think in terms of target
    end radius rather than radius step. The spiral will grow/shrink to reach
    the specified end radius.

    Args:
        states: List of states to arrange
        center: Center point of the spiral
        start_radius: Radius for first element
        end_radius: Radius for last element
        rotation: Base rotation offset in degrees
        clockwise: If True, spiral clockwise; if False, counterclockwise
        alignment: How to align each element
        element_rotation_offset: Additional rotation offset
        element_rotation_offset_fn: Function(angle) -> rotation offset.

    Examples:
        # Spiral outward from 50 to 200
        spiral_between_radii(states, start_radius=50, end_radius=200)

        # Spiral inward (negative step)
        spiral_between_radii(states, start_radius=200, end_radius=50)

        # Equivalent to spiral():
        # spiral_between_radii(states, start_radius=50, end_radius=200) with 5 states
        # == spiral(states, start_radius=50, radius_step=37.5) with 5 states
    """
    if not states:
        return []

    num_elements = len(states)

    # Calculate radius step to reach end_radius
    # For n elements: radius[i] = start_radius + i * radius_step
    # We want radius[n-1] = end_radius
    radius_step = (
        (end_radius - start_radius) / (num_elements - 1) if num_elements > 1 else 0
    )

    # Calculate angle step based on direction
    # Use 30 degrees as default (same as spiral default)
    angle_step = 30 if counter_clockwise else -30

    # Call canonical spiral function
    return spiral(
        states,
        center,
        start_radius=start_radius,
        radius_step=radius_step,
        start_angle=rotation,
        angle_step=angle_step,
        alignment=alignment,
        element_rotation_offset=element_rotation_offset,
        element_rotation_offset_fn=element_rotation_offset_fn,
    )


def spiral_equidistant(
    states: States,
    center: Point2D = Point2D(0, 0),
    start_radius: float = 50,
    end_radius: float = 200,
    total_angle: float = 360,
    start_angle: float = 0,
    alignment: ElementAlignment = ElementAlignment.PRESERVE,
    element_rotation_offset: float = 0,
    samples: int = 2000,
) -> States:
    """
    Arrange states along an Archimedean spiral with equal spacing by arc length.

    Unlike ``spiral`` (constant angle between elements), this keeps the distance
    between consecutive elements constant: elements are placed at equal
    arc-length intervals along a spiral whose radius varies linearly from
    ``start_radius`` (at ``start_angle``) to ``end_radius`` (at
    ``start_angle + total_angle``). Preserves all other state attributes while
    modifying position and rotation.

    Args:
        states: List of states to arrange
        center: Center point of the spiral
        start_radius: Radius at the first element
        end_radius: Radius at the last element
        total_angle: Signed angular sweep in degrees (+ counter-clockwise, − clockwise)
        start_angle: Angle in degrees of the first element
        alignment: How to align each element relative to the spiral.
                  PRESERVE keeps original rotation, LAYOUT aligns tangent to spiral
                  (bottom faces center), UPRIGHT keeps elements upright.
        element_rotation_offset: Additional rotation in degrees added to the alignment base.
        samples: Number of segments used to approximate the spiral arc length.
    """
    if not states:
        return []

    n = len(states)

    def point_at(t: float) -> tuple[float, float, float]:
        """Position and Cartesian angle (degrees) at fraction t in [0, 1]."""
        angle = start_angle + total_angle * t
        radius = start_radius + (end_radius - start_radius) * t
        angle_rad = math.radians(angle)
        x = center.x + radius * math.cos(angle_rad)
        y = center.y + radius * math.sin(angle_rad)
        return x, y, angle

    if n == 1:
        x, y, angle = point_at(0.0)
        positions = [(x, y, angle)]
    else:
        # Densely sample the spiral and build a cumulative arc-length table.
        steps = max(samples, n)
        pts = [point_at(k / steps) for k in range(steps + 1)]
        cumulative = [0.0]
        for k in range(1, steps + 1):
            dx = pts[k][0] - pts[k - 1][0]
            dy = pts[k][1] - pts[k - 1][1]
            cumulative.append(cumulative[-1] + math.hypot(dx, dy))
        total_length = cumulative[-1]

        # Walk the table, emitting a position at each equal arc-length target.
        positions = []
        seg = 0
        for i in range(n):
            target = total_length * i / (n - 1)
            # Stop at steps - 1 so seg + 1 stays in range; floating-point may put
            # the final target a hair beyond total_length.
            while seg < steps - 1 and cumulative[seg + 1] < target:
                seg += 1
            span = cumulative[seg + 1] - cumulative[seg]
            frac = 0.0 if span == 0 else (target - cumulative[seg]) / span
            frac = min(max(frac, 0.0), 1.0)
            x0, y0, a0 = pts[seg]
            x1, y1, a1 = pts[seg + 1]
            positions.append(
                (x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac, a0 + (a1 - a0) * frac)
            )

    result = []
    for state, (x, y, angle) in zip(states, positions):
        if alignment == ElementAlignment.LAYOUT:
            element_angle = angle - 90 + element_rotation_offset
        elif alignment == ElementAlignment.UPRIGHT:
            element_angle = element_rotation_offset
        else:
            element_angle = state.rotation
        result.append(replace(state, pos=Point2D(x, y), rotation=element_angle))

    return result
