"""Image renderer implementation using new architecture"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Tuple

from svan2d.component.registry import renderer
from svan2d.component.renderer.image import ImageRenderer
from svan2d.core.color import Color

from .base import State


class ImageFitMode(StrEnum):
    """
    Different modes for fitting images into the specified dimensions.

    Members:
        FIT: Scale the image to fit entirely within the bounds, maintaining aspect ratio.
        FILL: Scale the image to fill the bounds completely, cropping if necessary.
        CROP: Keep original size, crop to fit the bounds.
        STRETCH: Stretch the image to exact dimensions, changing aspect ratio if needed.
        ORIGINAL: Keep original size; may warn if the image doesn't fit the bounds.
        RANDOM_CROP: Randomly cut a section to fit the bounds, optionally rotated or flipped.
    """

    FIT = "fit"
    FILL = "fill"
    CROP = "crop"
    STRETCH = "stretch"
    ORIGINAL = "original"
    RANDOM_CROP = "random_crop"


@renderer(ImageRenderer)
@dataclass(frozen=True)
class ImageState(State):
    """State class for image elements"""

    href: str = ""  # Path or URL to the image file
    width: float | None = None  # Image width (None = use original image width)
    height: float | None = None  # Image height (None = use original image height)
    opacity: float = 1.0  # Image opacity (0.0 to 1.0)
    stroke_color: Optional[Color] = None  # Border color
    stroke_opacity: float = 1
    stroke_width: float = 0  # Border width
    fit_mode: ImageFitMode = ImageFitMode.FIT  # How to fit the image

    def __post_init__(self):
        super().__post_init__()
        self._none_color("stroke_color")
