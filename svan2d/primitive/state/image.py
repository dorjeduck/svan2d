"""Image renderer implementation using new architecture"""

from __future__ import annotations

import io
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from svan2d.primitive.registry import renderer, skia_renderer
from svan2d.primitive.renderer.image import ImageRenderer, ImageFitMode
from svan2d.core.color import Color

from .base import State

if TYPE_CHECKING:
    from PIL import Image as PILImage


@skia_renderer("svan2d.primitive.renderer.skia.image:ImageSkiaRenderer")
@renderer(ImageRenderer)
@dataclass(frozen=True)
class ImageState(State):
    """State class for image elements"""

    href: str = ""  # Path to the image file (used when data is None)
    data: bytes | None = None  # Raw image bytes; takes priority over href
    mime_type: str | None = None  # MIME type for data (e.g. "image/png")
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

    @classmethod
    def from_pil(
        cls, img: "PILImage.Image", *, format: str = "PNG", **kwargs
    ) -> "ImageState":
        """Build an ImageState from an in-memory PIL Image.

        The image is encoded once into bytes; no temp file is written.
        """
        buf = io.BytesIO()
        img.save(buf, format=format)
        return cls(data=buf.getvalue(), mime_type=f"image/{format.lower()}", **kwargs)
