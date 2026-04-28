"""Soft glow (halo) filter built from feGaussianBlur + feColorMatrix + feMerge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import drawsvg as dw

from .base import Filter

if TYPE_CHECKING:
    from svan2d.core.color import Color


@dataclass(frozen=True)
class GlowFilter(Filter):
    """Soft Gaussian halo around the source element.

    Recipe: blur the source alpha, re-colorize it via a color matrix that also
    multiplies the alpha by ``intensity`` (so the halo is visible even for
    large ``std_deviation`` values where a plain feDropShadow would be nearly
    invisible), then merge the original source on top.

    Args:
        std_deviation: Gaussian blur radius.
        color: Glow color.
        intensity: Alpha multiplier applied to the blurred shape (>= 1).
            Larger = brighter, more saturated halo. Clamped in SVG to [0, 1]
            after multiplication.
        opacity: Overall opacity of the halo (0-1).
        x, y, width, height: Optional SVG filter region (px or percentage
            strings like "-100%"). Must be generous enough to contain the
            blurred halo or it will clip into a visible rectangle.
    """

    std_deviation: float = 4.0
    color: "Color | None" = None
    intensity: float = 3.0
    opacity: float = 1.0
    x: str | float | None = None
    y: str | float | None = None
    width: str | float | None = None
    height: str | float | None = None

    def __post_init__(self):
        if self.std_deviation < 0:
            raise ValueError(f"std_deviation must be >= 0, got {self.std_deviation}")
        if self.intensity < 0:
            raise ValueError(f"intensity must be >= 0, got {self.intensity}")
        if not 0 <= self.opacity <= 1:
            raise ValueError(f"opacity must be between 0 and 1, got {self.opacity}")

    def to_drawsvg_items(self) -> list[dw.FilterItem]:
        """Return the three filter primitives that make up the glow.

        The base-class ``to_drawsvg`` returns only the first primitive; the
        renderer detects this method and appends all three when present.
        """
        from svan2d.core.color import Color

        c = self.color if self.color else Color("#ffffff")
        r = c.r / 255.0
        g = c.g / 255.0
        b = c.b / 255.0
        alpha_scale = self.intensity * self.opacity

        blur = dw.FilterItem(
            "feGaussianBlur",
            in_="SourceAlpha",
            stdDeviation=self.std_deviation,
            result="glowBlur",
        )
        matrix_values = (
            f"0 0 0 0 {r} "
            f"0 0 0 0 {g} "
            f"0 0 0 0 {b} "
            f"0 0 0 {alpha_scale} 0"
        )
        colorize = dw.FilterItem(
            "feColorMatrix",
            in_="glowBlur",
            type="matrix",
            values=matrix_values,
            result="glowColor",
        )
        merge = dw.FilterItem("feMerge")
        merge.append(dw.FilterItem("feMergeNode", in_="glowColor"))
        merge.append(dw.FilterItem("feMergeNode", in_="SourceGraphic"))
        return [blur, colorize, merge]

    def to_drawsvg(self) -> dw.FilterItem:
        """Abstract-method compliance. The renderer uses ``to_drawsvg_items``
        when available; this returns the first primitive so standalone use
        of the base Filter API doesn't break."""
        return self.to_drawsvg_items()[0]

    def interpolate(self, other: Filter, t: float):
        """Interpolate between two GlowFilter instances."""
        if not isinstance(other, GlowFilter):
            return self if t < 0.5 else other

        from svan2d.core.color import Color

        std_deviation = (
            self.std_deviation + (other.std_deviation - self.std_deviation) * t
        )
        intensity = self.intensity + (other.intensity - self.intensity) * t
        opacity = self.opacity + (other.opacity - self.opacity) * t

        default_color = Color("#ffffff")
        self_color = self.color if self.color else default_color
        other_color = other.color if other.color else default_color
        color = self_color.interpolate(other_color, t)

        region_src = self if t < 0.5 else other
        return GlowFilter(
            std_deviation=std_deviation,
            color=color,
            intensity=intensity,
            opacity=opacity,
            x=region_src.x,
            y=region_src.y,
            width=region_src.width,
            height=region_src.height,
        )
