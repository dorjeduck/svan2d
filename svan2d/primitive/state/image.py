"""Image renderer implementation using new architecture"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from svan2d.primitive.registry import renderer
from svan2d.primitive.renderer.image import ImageRenderer, ImageFitMode
from svan2d.core.color import Color

from .base import State


@renderer(ImageRenderer)
@dataclass(frozen=True)
class ImageState(State):
    """State class for image elements"""

    href: str = ""  # Path or URL to the image file
    width: float | None = None  # Image width (None = use original image width)
    height: float | None = None  # Image height (None = use original image height)
    opacity: float = 1.0  # Image opacity (0.0 to 1.0)
    stroke_color: Color | None = None  # Border color
    stroke_opacity: float = 1
    stroke_width: float = 0  # Border width
    fit_mode: ImageFitMode = ImageFitMode.FIT  # How to fit the image

    def __post_init__(self):
        super().__post_init__()
        self._none_color("stroke_color")
