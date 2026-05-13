"""Pause primitives for VScene timelines.

A pause is a flat plateau on the eased timeline: while raw frame time advances
through the pause window, eased time holds constant at the pause's `at`
position. Pauses are first-class on VScene via `VScene.add_pause(...)`.

The semantics here are *Regime 2 — absolute fraction*: each pause's `fraction`
is its share of the final rendered timeline, and pauses do not perturb each
other when added or removed (only motion absorbs the squeeze). The constraint
`Σ fractions < 1` is enforced at build time with `PauseFractionError`.
"""

from svan2d.transition.pause.pause_descriptor import PauseDescriptor
from svan2d.transition.pause.pause_fraction_error import PauseFractionError
from svan2d.transition.pause.pause_easing import build_pause_easing
from svan2d.transition.pause.pause_opacity import (
    pause_opacity,
    local_pause_t,
)

__all__ = [
    "PauseDescriptor",
    "PauseFractionError",
    "build_pause_easing",
    "pause_opacity",
    "local_pause_t",
]
