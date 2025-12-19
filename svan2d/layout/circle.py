"""Circle layout state function"""

import math
from typing import List, Optional, Callable
from dataclasses import replace

from svan2d.component.state.base import States
from svan2d.core.point2d import Point2D
from .enums import ElementAlignment


def circle(
    states: States,
    radius: float = 100,
    rotation: float = 0,
    center: Point2D = Point2D(0, 0),
    clockwise: bool = True,
    angles: Optional[List[float]] = None,
    alignment: ElementAlignment = ElementAlignment.PRESERVE,
    element_rotation_offset: float = 0,
    element_rotation_offset_fn: Optional[Callable[[float], float]] = None,
    radius_fn: Optional[Callable[[int, float], float]] = None,
) -> States:

    if not states:
        return []

    result = []

    # Use custom angles if provided, otherwise calculate even distribution
    if angles is not None:
        if len(angles) < len(states):
            raise ValueError(
                f"Length of angles ({len(angles)}) must be equal or bigger than length of states ({len(states)})"
            )
        element_angles = angles
    else:
        # Calculate even distribution
        num_elements = len(states)
        angle_step = 360 / num_elements
        element_angles = [
            i * angle_step if clockwise else -i * angle_step
            for i in range(num_elements)
        ]

    # Position each element at its calculated angle
    for i, state in enumerate(states):
        angle = rotation + element_angles[i]

        # Convert to radians for math functions
        angle_rad = math.radians(angle)

        # Calculate radius for this element
        r = radius_fn(i, radius) if radius_fn else radius

        # Calculate position (note: y is flipped because SVG y increases downward)
        x = center.x + r * math.sin(angle_rad)
        y = center.y - r * math.cos(angle_rad)

        # Calculate additional rotation (function-based or static)
        additional_rotation = (
            element_rotation_offset_fn(angle)
            if element_rotation_offset_fn
            else element_rotation_offset
        )

        # Calculate element rotation based on alignment mode
        if alignment == ElementAlignment.PRESERVE:
            element_angle = state.rotation
        elif alignment == ElementAlignment.LAYOUT:
            # Align with layout direction (tangent to circle) + additional rotation
            element_angle = angle + additional_rotation
        elif alignment == ElementAlignment.UPRIGHT:
            # Start from upright position + additional rotation
            element_angle = additional_rotation
        else:
            element_angle = state.rotation

        # Create new state with circular position and rotation, preserving all other attributes
        new_state = replace(state, pos=Point2D(x, y), rotation=element_angle)
        result.append(new_state)

    return result


def circle_between_points(
    states: States,
    p1: Point2D,
    p2: Point2D,
    rotation: float = 0,
    clockwise: bool = True,
    alignment: ElementAlignment = ElementAlignment.PRESERVE,
    element_rotation_offset: float = 0,
    angles: Optional[List[float]] = None,
    radius_fn: Optional[Callable[[int, float], float]] = None,
    element_rotation_offset_fn: Optional[Callable[[float], float]] = None,
) -> States:
    """
    Arrange states in a circular formation with diameter defined by two points.

    Alternative specification to circle() for users who think in terms of diameter endpoints.
    The circle's center will be at the midpoint between the two points, and the radius will
    be half the distance between them.

    Args:
        states: List of states to arrange
        p1: point 1
        p2: point 2
        rotation: Rotation offset in degrees
        clockwise: If True, arrange clockwise; if False, counterclockwise
        alignment: How to align each element relative to the circle
        element_rotation_offset: Additional rotation in degrees added to the alignment base
        angles: Optional list of specific angles in degrees for each element
        radius_fn: Function that takes (index, default_radius) and returns custom radius
        element_rotation_offset_fn: Function that takes position angle and returns rotation offset

    Returns:
        New list of states with circular positions

    Raises:
        ValueError: If points are identical (zero diameter)

    Examples:
        # Circle with diameter from origin to (200, 0) - radius 100
        circle_between_points(states, 0, 0, 200, 0)

        # Circle with diagonal diameter
        circle_between_points(states, -100, -100, 100, 100)

        # Equivalent to circle() with center and radius:
        # circle_between_points(states, 0, 0, 200, 0)
        # == circle(states, cpos=Point2D(100, 0), cy=0, radius=100)
    """
    if not states:
        return []

    # Calculate center and radius from diameter endpoints

    distance = p1.distance_to(p2)

    if distance < 1e-10:
        raise ValueError(
            f"Diameter endpoints ({p1.x}, {p1.y}) and ({p2.x}, {p2.y}) are identical. "
            "Cannot create a circle with zero radius."
        )

    center = p1.center_to(p2)

    radius = distance / 2

    # Call canonical circle function
    return circle(
        states,
        radius=radius,
        rotation=rotation,
        center=center,
        clockwise=clockwise,
        angles=angles,
        alignment=alignment,
        element_rotation_offset=element_rotation_offset,
        element_rotation_offset_fn=element_rotation_offset_fn,
        radius_fn=radius_fn,
    )


def circle_through_points(
    states: States,
    p1: Point2D,
    p2: Point2D,
    p3: Point2D,
    rotation: float = 0,
    clockwise: bool = True,
    alignment: ElementAlignment = ElementAlignment.PRESERVE,
    element_rotation_offset: float = 0,
    angles: Optional[List[float]] = None,
    radius_fn: Optional[Callable[[int, float], float]] = None,
    element_rotation_offset_fn: Optional[Callable[[float], float]] = None,
) -> States:
    """
    Arrange states in a circular formation passing through three given points.

    Calculates the circumcircle (circle passing through three points) and arranges
    states along it. This is useful when you know specific points the circle should
    pass through rather than its center and radius.

    Args:
        states: List of states to arrange
        p1 : Point 1
        p2 : Point 2
        p3 : Point 3
        rotation: Rotation offset in degrees
        clockwise: If True, arrange clockwise; if False, counterclockwise
        alignment: How to align each element relative to the circle
        element_rotation_offset: Additional rotation in degrees added to the alignment base
        angles: Optional list of specific angles in degrees for each element
        radius_fn: Function that takes (index, default_radius) and returns custom radius
        element_rotation_offset_fn: Function that takes position angle and returns rotation offset

    Returns:
        New list of states with circular positions

    Raises:
        ValueError: If the three points are collinear (no unique circle)
        ValueError: If any two points are identical

    Examples:
        # Circle through three points forming a triangle
        circle_through_points(states, 0, 100, 100, 0, 0, -100)

        # Right triangle points
        circle_through_points(states, 0, 0, 100, 0, 0, 100)
    """
    if not states:
        return []

    # Check for duplicate points
    if (
        (abs(p1.x - p2.x) < 1e-10 and abs(p1.y - p2.y) < 1e-10)
        or (abs(p2.x - p3.x) < 1e-10 and abs(p2.y - p3.y) < 1e-10)
        or (abs(p1.x - p3.x) < 1e-10 and abs(p1.y - p3.y) < 1e-10)
    ):
        raise ValueError("Cannot create circle: two or more points are identical")

    # Calculate circumcircle using determinant method
    # See: https://en.wikipedia.org/wiki/Circumscribed_circle
    D = 2 * (p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y))

    if abs(D) < 1e-10:
        raise ValueError(
            f"Points ({p1.x}, {p1.y}), ({p2.x}, {p2.y}), ({p3.x}, {p3.y}) are collinear. "
            "Cannot define a unique circle through collinear points."
        )

    # Calculate circumcenter coordinates
    ux = (
        (p1.x * p1.x + p1.y * p1.y) * (p2.y - p3.y)
        + (p2.x * p2.x + p2.y * p2.y) * (p3.y - p1.y)
        + (p3.x * p3.x + p3.y * p3.y) * (p1.y - p2.y)
    ) / D
    uy = (
        (p1.x * p1.x + p1.y * p1.y) * (p3.x - p2.x)
        + (p2.x * p2.x + p2.y * p2.y) * (p1.x - p3.x)
        + (p3.x * p3.x + p3.y * p3.y) * (p2.x - p1.x)
    ) / D

    cx = ux
    cy = uy
    radius = math.sqrt((p1.x - ux) ** 2 + (p1.y - uy) ** 2)

    # Call canonical circle function
    return circle(
        states,
        radius=radius,
        rotation=rotation,
        center=Point2D(cx, cy),
        clockwise=clockwise,
        angles=angles,
        alignment=alignment,
        element_rotation_offset=element_rotation_offset,
        element_rotation_offset_fn=element_rotation_offset_fn,
        radius_fn=radius_fn,
    )
