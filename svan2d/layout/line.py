"""Line layout state function"""

import math
from dataclasses import replace

from svan2d.component.state.base import States
from svan2d.core.point2d import Point2D

from .enums import ElementAlignment


def line(
    states: States,
    spacing: float = 100,
    rotation: float = 0,
    center: Point2D = Point2D(0, 0),
    distances: list[float] | None = None,
    alignment: ElementAlignment = ElementAlignment.PRESERVE,
    element_rotation_offset: float = 0,
) -> States:
    """
    Arrange states in a straight line formation.

    Positions elements along a straight line with configurable spacing, rotation, and center point.
    For odd numbers of elements, one element is placed at the center. For even numbers,
    elements are distributed symmetrically around the center point.
    Preserves all other state attributes (color, scale, opacity, etc.) while only
    modifying x and y positions.

    Args:
        states: List of states to arrange
        spacing: Distance between adjacent elements. Only used when distances is None.
        rotation: Angle of the line in degrees (0° = horizontal right, 90° = vertical down)
        center: Center point of the line
        distances: Optional list of specific distances from center for each element.
                  If provided, overrides automatic distribution and spacing parameter.
                  Positive values = forward along line, negative = backward along line.
                  List length should match states length.
        alignment: How to align each element relative to the line.
                  PRESERVE keeps original rotation, LAYOUT aligns parallel to line,
                  UPRIGHT starts from vertical position.
        element_rotation_offset: Additional rotation in degrees added to the alignment base.

    Examples:
        # Even spacing (automatic distribution)
        line(states, spacing=50, rotation=0)

        # Explicit distances from center
        line(states, distances=[-100, -20, 50, 150])

        # Elements aligned with line direction
        line(states, rotation=45, alignment=ElementAlignment.LAYOUT)
    """
    if not states:
        return []

    result = []

    # Use explicit distances if provided, otherwise calculate even distribution
    if distances is not None:
        if len(distances) < len(states):
            raise ValueError(
                f"Length of distances ({len(distances)}) must be equal or bigger than length of states ({len(states)})"
            )
        line_positions = distances
    else:
        # Calculate automatic distribution
        num_elements = len(states)

        if num_elements % 2 == 1:
            # Odd number of elements - one at center
            center_index = num_elements // 2
            line_positions = [(i - center_index) * spacing for i in range(num_elements)]
        else:
            # Even number of elements - symmetric around center
            line_positions = [
                (i - (num_elements - 1) / 2) * spacing for i in range(num_elements)
            ]

    # Convert line positions to 2D coordinates
    rotation_rad = math.radians(rotation)
    cos_rotation = math.cos(rotation_rad)
    sin_rotation = math.sin(rotation_rad)

    for i, state in enumerate(states):
        line_pos = line_positions[i]

        # Calculate position along the line
        x = center.x + line_pos * cos_rotation
        y = center.y + line_pos * sin_rotation

        # Calculate element rotation based on alignment mode
        if alignment == ElementAlignment.PRESERVE:
            element_rot = state.rotation
        elif alignment == ElementAlignment.LAYOUT:
            # Align with line direction + additional rotation
            element_rot = rotation + element_rotation_offset
        elif alignment == ElementAlignment.UPRIGHT:
            # Start from upright position + additional rotation
            element_rot = element_rotation_offset
        else:
            element_rot = state.rotation

        # Create new state with line position and rotation
        new_state = replace(state, pos=Point2D(x, y), rotation=element_rot)
        result.append(new_state)

    return result
