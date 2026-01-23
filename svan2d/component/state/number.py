"""Number state implementation for displaying formatted numbers"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from svan2d.component.registry import renderer
from svan2d.component.renderer.number import NumberRenderer
from svan2d.component.state.text import TextState


class NumberFormat(StrEnum):
    """Number formatting modes"""

    INTEGER = "integer"  # No decimal places (rounds to nearest int)

    # experimental ...
    AUTO = "auto"  # Shows decimals only when needed (e.g., 5 vs 5.25)
    FIXED = "fixed"  # Always shows exactly N decimal places (e.g., 5.00)
    AUTO_ALIGNED = "auto_aligned"  # Like AUTO but keeps decimal point position fixed
    FIXED_ALIGNED = "fixed_aligned"  # Like FIXED but keeps decimal point position fixed


@renderer(NumberRenderer)
@dataclass(frozen=True)
class NumberState(TextState):
    """State class for number display with formatting

    Displays a numeric value with configurable decimal precision.
    The actual number to display is stored in the 'value' field,
    while 'text' is auto-generated based on formatting rules.

    For decimal point alignment (AUTO_ALIGNED and FIXED_ALIGNED modes),
    the number is rendered as two separate text elements (integer and
    decimal parts) positioned to keep the decimal point at the same location.

    Examples:
        # Integer display (no decimals)
        NumberState(value=42, format=NumberFormat.INTEGER)  # "42"

        # Auto formatting (decimals when needed)
        NumberState(value=5.0, format=NumberFormat.AUTO)    # "5"
        NumberState(value=5.25, format=NumberFormat.AUTO)   # "5.25"

        # Auto with aligned decimal point (keeps "." position fixed)
        NumberState(value=5.0, format=NumberFormat.AUTO_ALIGNED)   # "5" (but positioned as if "5.")
        NumberState(value=5.25, format=NumberFormat.AUTO_ALIGNED)  # "5.25" (decimal point at same x)

        # Fixed precision
        NumberState(value=5, format=NumberFormat.FIXED, decimals=2)  # "5.00"
        NumberState(value=5.678, decimals=2)  # "5.68" (default is FIXED)

        # Fixed precision with aligned decimal point
        NumberState(value=5, format=NumberFormat.FIXED_ALIGNED, decimals=2)     # "5.00"
        NumberState(value=99.5, format=NumberFormat.FIXED_ALIGNED, decimals=2)  # "99.50"
        # Decimal point stays at same x position

    Attributes:
        value: The numeric value to display
        format: How to format the number (INTEGER, AUTO, AUTO_ALIGNED, FIXED, FIXED_ALIGNED)
        decimals: Number of decimal places (for FIXED/FIXED_ALIGNED modes, default 2)
        max_decimals: Maximum decimals for AUTO_ALIGNED (default 2)
        prefix: Optional text before number (e.g., "$")
        suffix: Optional text after number (e.g., "px", "%")
        thousands_separator: Optional separator for thousands (e.g., "," for 1,000,000)
    """

    value: float = 0.0
    format: NumberFormat = NumberFormat.FIXED
    decimals: int = 2  # Used when format=FIXED or FIXED_ALIGNED
    max_decimals: int = 2  # Maximum decimals for AUTO_ALIGNED
    prefix: str = ""
    suffix: str = ""
    thousands_separator: str = ""  # e.g., "," for 1,000,000

    # Override text_anchor for aligned formats (will be ignored for aligned rendering)
    text_anchor: str = "middle"

    # Internal fields for aligned rendering (don't set manually)
    _integer_part: str = ""
    _decimal_part: str = ""
    _has_decimals: bool = False

    # Override text to be auto-generated (user shouldn't set this directly)
    text: str = ""

    def __post_init__(self):
        """Generate formatted text from value"""
        super().__post_init__()

        # Format the number based on settings
        if self.format in (NumberFormat.AUTO_ALIGNED, NumberFormat.FIXED_ALIGNED):
            # Split into integer and decimal parts for aligned rendering
            formatted_number = self._format_value()

            # Split on decimal point
            if "." in formatted_number:
                int_part, dec_part = formatted_number.split(".", 1)
                self._set_field("_integer_part", int_part)
                self._set_field("_decimal_part", "." + dec_part)
                self._set_field("_has_decimals", True)
            else:
                self._set_field("_integer_part", formatted_number)
                self._set_field("_decimal_part", "")
                self._set_field("_has_decimals", False)

            # Set text to full number for fallback rendering
            formatted_text = f"{self.prefix}{formatted_number}{self.suffix}"
        else:
            # Standard formatting - single text element
            formatted_number = self._format_value()
            formatted_text = f"{self.prefix}{formatted_number}{self.suffix}"

        # Set the text field with formatted result
        self._set_field("text", formatted_text)

    def _apply_thousands_separator(self, formatted: str) -> str:
        """Apply thousands separator to the integer part of a formatted number."""
        if not self.thousands_separator:
            return formatted

        # Split into integer and decimal parts
        if "." in formatted:
            int_part, dec_part = formatted.split(".", 1)
            dec_part = "." + dec_part
        else:
            int_part = formatted
            dec_part = ""

        # Handle negative numbers
        negative = int_part.startswith("-")
        if negative:
            int_part = int_part[1:]

        # Add separator every 3 digits from the right
        result = ""
        for i, digit in enumerate(reversed(int_part)):
            if i > 0 and i % 3 == 0:
                result = self.thousands_separator + result
            result = digit + result

        if negative:
            result = "-" + result

        return result + dec_part

    def _format_value(self) -> str:
        """Format the numeric value based on format settings"""
        if self.format == NumberFormat.INTEGER:
            # Round to nearest integer
            result = str(round(self.value))

        elif (
            self.format == NumberFormat.AUTO or self.format == NumberFormat.AUTO_ALIGNED
        ):
            # Show decimals only if not a whole number
            if self.value == int(self.value):
                result = str(int(self.value))
            else:
                # Limit decimals to max_decimals for AUTO_ALIGNED
                if self.format == NumberFormat.AUTO_ALIGNED:
                    # Format with max decimals, then remove trailing zeros
                    result = f"{self.value:.{self.max_decimals}f}"
                    # Remove trailing zeros after decimal point
                    if "." in result:
                        result = result.rstrip("0").rstrip(".")
                else:
                    # Remove trailing zeros (standard AUTO behavior)
                    result = f"{self.value:g}"

        elif (
            self.format == NumberFormat.FIXED
            or self.format == NumberFormat.FIXED_ALIGNED
        ):
            # Always show exactly N decimal places
            result = f"{self.value:.{self.decimals}f}"

        else:
            # Fallback to AUTO behavior
            result = f"{self.value:g}"

        return self._apply_thousands_separator(result)
