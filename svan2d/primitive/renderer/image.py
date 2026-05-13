"""Image renderer implementation using new architecture"""

from __future__ import annotations

from enum import StrEnum
import io
import logging
import random
from typing import TYPE_CHECKING

import drawsvg as dw
from PIL import Image

from .base import Renderer

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

if TYPE_CHECKING:
    from ..state.image import  ImageState


class ImageRenderer(Renderer):
    """Renderer class for rendering image elements"""

    def _apply_random_transforms(self, img: Image.Image) -> Image.Image:
        """Apply random rotation and flips to image for diversity

        Args:
            img: PIL Image to transform

        Returns:
            Transformed PIL Image
        """
        # Random 90-degree rotation (0, 90, 180, or 270 degrees)
        rotation_choice = random.choice(
            [
                None,
                Image.Transpose.ROTATE_90,
                Image.Transpose.ROTATE_180,
                Image.Transpose.ROTATE_270,
            ]
        )
        if rotation_choice is not None:
            img = img.transpose(rotation_choice)

        # Random horizontal flip (50% chance)
        if random.random() > 0.5:
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        # Random vertical flip (50% chance)
        if random.random() > 0.5:
            img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        return img

    def _random_crop_image(
        self,
        img: Image.Image,
        target_width: int,
        target_height: int,
        mime_hint: str,
        source_label: str,
    ) -> tuple[bytes, str]:
        """Randomly crop and transform an opened PIL image to fit target dimensions.

        Returns (image_data_bytes, mime_type).
        """
        img_width, img_height = img.size

        crop_width = min(int(target_width), img_width)
        crop_height = min(int(target_height), img_height)

        if crop_width < img_width or crop_height < img_height:
            left = random.randint(0, img_width - crop_width)
            top = random.randint(0, img_height - crop_height)
            img = img.crop((left, top, left + crop_width, top + crop_height))
        else:
            logging.warning(
                f"Image {source_label} ({img_width}x{img_height}) is smaller than target crop size ({target_width}x{target_height}). Using full image."
            )

        img = self._apply_random_transforms(img)

        buffer = io.BytesIO()
        img_format = img.format if img.format else "PNG"
        img.save(buffer, format=img_format)
        return buffer.getvalue(), mime_hint

    def _calculate_dimensions(
        self,
        href: str,
        target_width: float,
        target_height: float,
        original_width: int,
        original_height: int,
        fit_mode: ImageFitMode,
    ) -> tuple[float, float, bool]:
        """Calculate final image dimensions based on fit mode

        Args:
            target_width: Desired width from state
            target_height: Desired height from state
            original_width: Original image width in pixels
            original_height: Original image height in pixels

        Returns:
            Tuple of (final_width, final_height, needs_clipping)
        """
        if fit_mode == ImageFitMode.FIT:
            # Scale to fit entirely within bounds (preserve aspect ratio)
            scale_x = target_width / original_width
            scale_y = target_height / original_height
            scale = min(scale_x, scale_y)
            return (original_width * scale, original_height * scale, False)

        elif fit_mode == ImageFitMode.FILL:
            # Scale to fill bounds completely, crop if needed (preserve aspect ratio)
            scale_x = target_width / original_width
            scale_y = target_height / original_height
            scale = max(scale_x, scale_y)
            return (original_width * scale, original_height * scale, True)

        elif fit_mode == ImageFitMode.CROP:
            # Keep original size, crop to bounds
            return (original_width, original_height, True)

        elif fit_mode == ImageFitMode.STRETCH:
            # Stretch to exact dimensions (changes aspect ratio)
            logging.warning(
                f"Image {href} aspect ratio will be changed due to STRETCH mode"
            )
            return (target_width, target_height, False)

        elif fit_mode == ImageFitMode.ORIGINAL:
            # Keep original size, warn if doesn't fit
            if original_width > target_width or original_height > target_height:
                logging.warning(
                    f"Image {href} ({original_width}x{original_height}) is larger than target size ({target_width}x{target_height})"
                )
            elif original_width < target_width or original_height < target_height:
                logging.warning(
                    f"Image {href} ({original_width}x{original_height}) is smaller than target size ({target_width}x{target_height})"
                )
            return (original_width, original_height, False)

        elif fit_mode == ImageFitMode.RANDOM_CROP:
            # Random crop will be handled in _render_core
            # Return target dimensions, no clipping needed (image will already be cropped)
            return (target_width, target_height, False)

        else:
            # Default to FIT mode
            scale_x = target_width / original_width
            scale_y = target_height / original_height
            scale = min(scale_x, scale_y)
            return (original_width * scale, original_height * scale, False)

    def _render_core(
        self, state: "ImageState", drawing: dw.Drawing | None = None
    ) -> dw.Group:
        """Render the image renderer without transforms

        Args:
            state: "ImageState" containing rendering attributes

        Returns:
            drawsvg Group containing the image renderer
        """

        # Create a group to hold the image
        group = dw.Group()

        # Read image data for embedding first to get original dimensions
        try:
            import mimetypes

            from_bytes = state.data is not None
            source_label = "<in-memory>" if from_bytes else state.href

            if from_bytes:
                default_mime = state.mime_type or "image/png"
            else:
                guessed, _ = mimetypes.guess_type(state.href)
                default_mime = guessed or "image/png"

            def _open_pil() -> Image.Image:
                if from_bytes:
                    return Image.open(io.BytesIO(state.data))
                return Image.open(state.href)

            # Get original image dimensions first
            try:
                with _open_pil() as img:
                    original_width, original_height = img.size
            except Exception:
                logging.warning(
                    "Could not determine original image size from '%s'. Using defaults.",
                    source_label,
                )
                original_width, original_height = 100, 100

            # Use original dimensions if width/height not specified in state
            target_width = state.width if state.width is not None else original_width
            target_height = (
                state.height if state.height is not None else original_height
            )

            # Handle RANDOM_CROP mode with special processing
            if state.fit_mode == ImageFitMode.RANDOM_CROP:
                try:
                    with _open_pil() as img:
                        image_data, mime_type = self._random_crop_image(
                            img,
                            int(target_width),
                            int(target_height),
                            default_mime,
                            source_label,
                        )
                except Exception as e:
                    logging.error(
                        f"Failed to apply random crop to {source_label}: {e}"
                    )
                    # Fall back to embedding the unmodified bytes
                    if from_bytes:
                        image_data = state.data
                    else:
                        with open(state.href, "rb") as image_file:
                            image_data = image_file.read()
                    mime_type = default_mime
            else:
                if from_bytes:
                    image_data = state.data
                else:
                    with open(state.href, "rb") as image_file:
                        image_data = image_file.read()
                mime_type = default_mime

            # Calculate final dimensions based on fit mode
            final_width, final_height, clip_rect = self._calculate_dimensions(
                source_label,
                target_width,
                target_height,
                original_width,
                original_height,
                state.fit_mode,
            )

            # Position image based on final dimensions
            final_image_x = -final_width / 2
            final_image_y = -final_height / 2

            image_kwargs = {
                "x": final_image_x,
                "y": final_image_y,
                "width": final_width,
                "height": final_height,
                "opacity": state.opacity,
                "data": image_data,  # Pass raw bytes - drawsvg will handle base64 encoding
                "mime_type": mime_type,
            }

            # Add clipping if needed for CROP or FILL modes
            if clip_rect:
                import uuid

                clip_id = f"clip_{uuid.uuid4().hex[:8]}"

                clip_path = dw.ClipPath()
                clip_path.args["id"] = clip_id

                # Clip rectangle should be the target bounds, centered
                clip_rect_elem = dw.Rectangle(
                    x=-target_width / 2,
                    y=-target_height / 2,
                    width=target_width,
                    height=target_height,
                )
                clip_path.append(clip_rect_elem)
                group.append(clip_path)

                # Apply clipping to the image
                image_kwargs["clip_path"] = f"url(#{clip_id})"

        except Exception as e:
            # Placeholder rectangle if image fails to load
            placeholder = dw.Rectangle(
                x=-100 / 2,
                y=-100 / 2,
                width=100,
                height=100,
                fill="gray",
                stroke="red",
                stroke_width=2,
            )
            group.append(placeholder)

            # 2. Add the actual error message as SVG text
            # We use a small font size and wrap the error string 'e'
            error_message = f"Error: {str(e)}"  # type: ignore
            error_text = dw.Text(
                text=error_message,
                font_size=8,
                x=-45,  # Position inside the rectangle
                y=0,  # Middle of the rectangle
                fill="white",
            )
            group.append(error_text)

            return group  # Skip image rendering on error

        # Apply fill and stroke styling
        self._set_fill_and_stroke_kwargs(state, image_kwargs, drawing)

        # Create the image element
        image = dw.Image(**image_kwargs)
        group.append(image)

        return group
