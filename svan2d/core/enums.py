"""Shared enums for svan2d."""

from enum import StrEnum


class Origin(StrEnum):
    """Origin mode for scene coordinate system."""

    CENTER = "center"
    TOP_LEFT = "top-left"
