"""Em: a length given as a share of the font size, as SVG and CSS write `0.04em`."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Em:
    """A length in em, `value` times the font size of the text it belongs to."""

    value: float

    @classmethod
    def parse(cls, text: str) -> Em:
        """`"0.04em"` as Em(0.04); anything else is an error."""
        number = text.strip().removesuffix("em")
        if number == text.strip():
            raise ValueError(f"{text!r} is not a length in em, such as '0.04em'")
        try:
            return cls(float(number))
        except ValueError:
            raise ValueError(
                f"{text!r} is not a length in em, such as '0.04em'"
            ) from None

    def px(self, font_size: float) -> float:
        """This length in pixels at `font_size`."""
        return self.value * font_size


def letter_spacing_px(spacing: float | Em | None, font_size: float) -> float:
    """A letter spacing in pixels at `font_size`: em is a share of it, a number
    is pixels already, and no spacing is none at all."""
    if isinstance(spacing, Em):
        return spacing.px(font_size)
    return float(spacing or 0)


def scale_letter_spacing(spacing: float | Em, factor: float) -> float | Em:
    """The spacing for its text drawn `factor` times the size: pixels scale
    with it, em follows the font size by itself."""
    if isinstance(spacing, Em):
        return spacing
    return spacing * factor
