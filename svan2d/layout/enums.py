"""Enumerations for layout configuration."""

from enum import StrEnum


class ElementAlignment(StrEnum):
    """
    Element alignment modes for layout functions.

    Members:
        PRESERVE: Keep the element's original rotation.
        LAYOUT: Align with the layout direction (e.g., tangent to a circle, parallel to a line).
        UPRIGHT: Align starting from an upright position (0° rotation).
    """

    PRESERVE = "preserve"
    LAYOUT = "layout"
    UPRIGHT = "upright"
