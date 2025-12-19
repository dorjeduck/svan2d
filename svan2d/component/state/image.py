"""Image renderer implementation using new architecture"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
from enum import StrEnum


from .base import State
from svan2d.component.registry import renderer
from svan2d.component.renderer.image import ImageRenderer
from svan2d.transition import easing
from svan2d.core.color import Color


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
    width: Optional[float] = None  # Image width (None = use original image width)
    height: Optional[float] = None  # Image height (None = use original image height)
    opacity: float = 1.0  # Image opacity (0.0 to 1.0)
    stroke_color: Optional[Color] = None  # Border color
    stroke_opacity: float = 1
    stroke_width: float = 0  # Border width
    fit_mode: ImageFitMode = ImageFitMode.FIT  # How to fit the image

    DEFAULT_EASING = {
        **State.DEFAULT_EASING,
        "width": easing.in_out,
        "height": easing.in_out,
    }

    def __post_init__(self):
        super().__post_init__()
        self._none_color("stroke_color")

