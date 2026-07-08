"""Pause descriptor: where on the timeline a pause sits and how long it is."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from svan2d.velement import VElement
    from svan2d.vscene.vscene import VScene


PauseOverlay: TypeAlias = "VElement | VScene"


@dataclass(frozen=True)
class PauseDescriptor:
    """A single pause on a VScene's timeline.

    Attributes:
        at: Position on the *unpaused* timeline in [0, 1] where the pause
            occurs. Multiple pauses can share the same `at`.
        fraction: Share of the *final rendered* timeline this pause occupies,
            in (0, 1). The sum of fractions across all pauses on a scene must
            be strictly less than 1.
        overlay: Optional element or sub-scene shown during the pause window.
            A VElement is held at its base state; a VScene receives a local
            timeline mapping 0..1 across the pause window.
        fade: Fraction of the pause window used for fade-in / fade-out at each
            edge. 0.0 means hard cut; 0.5 means full triangular ramp.
    """

    at: float
    fraction: float
    overlay: PauseOverlay | None = None
    fade: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.at <= 1.0:
            raise ValueError(f"Pause `at` must be in [0, 1], got {self.at}")
        if not 0.0 < self.fraction < 1.0:
            raise ValueError(
                f"Pause `fraction` must be in (0, 1), got {self.fraction}"
            )
        if not 0.0 <= self.fade <= 0.5:
            raise ValueError(f"Pause `fade` must be in [0, 0.5], got {self.fade}")
