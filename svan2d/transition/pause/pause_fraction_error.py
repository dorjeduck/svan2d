"""Error raised when pause fractions overflow the timeline."""

from __future__ import annotations


class PauseFractionError(ValueError):
    """Raised when the sum of pause fractions on a VScene reaches or exceeds 1.0.

    Pauses occupy `fraction` of the final rendered timeline; motion takes the
    remainder `1 - Σ fractions`. When `Σ fractions >= 1` there is no room left
    for motion, which is treated as an authoring error rather than silently
    rescaled.
    """

    def __init__(self, fractions: list[float]) -> None:
        self.fractions = list(fractions)
        self.total = sum(self.fractions)
        super().__init__(
            f"Pause fractions sum to {self.total:.4f} (>= 1.0); "
            f"no room left for motion. Fractions: {self.fractions}"
        )
