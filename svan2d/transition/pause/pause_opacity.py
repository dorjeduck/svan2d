"""Pause window helpers: fade opacity and local time mapping.

These free functions translate a *raw* (un-eased) frame time into:
- an opacity in [0, 1] for an overlay element/scene during a pause window,
  with a triangular fade-in / hold / fade-out shape;
- a local time in [0, 1] across the pause window, for animated overlays.

Inputs are raw timeline values (the input to a `VScene.timeline_easing`).
"""

from __future__ import annotations


def pause_opacity(
    raw_t: float,
    window: tuple[float, float],
    fade: float,
) -> float:
    """Return overlay opacity at `raw_t` for a pause window.

    Args:
        raw_t: Raw (un-eased) frame time in [0, 1].
        window: `(start, end)` of the pause in raw time.
        fade: Fraction of the window used for fade-in and fade-out at each
            edge. 0.0 means hard cut. Values in (0, 0.5] give a triangular
            ramp on each side; 0.5 gives a full triangle (no flat hold).

    Returns:
        Opacity in [0, 1]. 0 outside the window, ramps over `fade × width` at
        each edge, 1.0 in the middle.
    """
    start, end = window
    width = end - start
    if width <= 0.0:
        return 0.0
    if raw_t < start or raw_t > end:
        return 0.0
    if fade <= 0.0:
        return 1.0

    fade_len = fade * width
    if fade_len <= 0.0:
        return 1.0

    # Fade-in
    if raw_t < start + fade_len:
        return (raw_t - start) / fade_len
    # Fade-out
    if raw_t > end - fade_len:
        return (end - raw_t) / fade_len
    return 1.0


def local_pause_t(
    raw_t: float,
    window: tuple[float, float],
) -> float:
    """Return local time in [0, 1] across a pause window.

    Args:
        raw_t: Raw (un-eased) frame time.
        window: `(start, end)` of the pause in raw time.

    Returns:
        Local time `(raw_t - start) / (end - start)`, clamped to [0, 1].
        Returns 0.0 if the window has zero width.
    """
    start, end = window
    width = end - start
    if width <= 0.0:
        return 0.0
    if raw_t <= start:
        return 0.0
    if raw_t >= end:
        return 1.0
    return (raw_t - start) / width
