"""Proportional scaling utility for solar system showcases."""

import math


def scale_values(
    values: dict[str, float], scaling: str, fit_px: float
) -> dict[str, float]:
    """Scale values proportionally. Largest maps to fit_px, rest proportional.

    Args:
        values: Name-to-real-value mapping (e.g. km or AU).
        scaling: "linear", "sqrt", "cbrt", or "log".
        fit_px: Pixel size for the largest value.

    Returns:
        Name-to-pixel mapping with honest proportions (no min/max clamping).
    """
    if not values:
        return {}

    max_val = max(values.values())
    if max_val == 0:
        return {k: 0.0 for k in values}

    result: dict[str, float] = {}
    for name, val in values.items():
        if scaling == "sqrt":
            ratio = math.sqrt(val) / math.sqrt(max_val)
        elif scaling == "cbrt":
            ratio = math.cbrt(val) / math.cbrt(max_val)
        elif scaling == "log":
            ratio = math.log1p(val) / math.log1p(max_val)
        else:  # linear
            ratio = val / max_val
        result[name] = ratio * fit_px

    return result
