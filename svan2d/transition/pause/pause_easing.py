"""Build a piecewise-linear timeline easing from a list of pauses.

Regime 2 semantics: each pause's `fraction` is a share of the final rendered
timeline. Motion gets `M = 1 - Σ fractions`; motion sub-segments between
pauses default to uniform velocity, but `motion_speeds` lets each motion
segment claim a relative share. `Σ fractions >= 1` raises
`PauseFractionError`.

The builder returns:
- `easing(raw_t) -> eased_t`: the timeline easing to set on `VScene`.
- `windows`: list of `(raw_start, raw_end)` tuples, one per pause descriptor,
  in the original input order. These are the raw-time intervals during which
  eased time is held constant — used by overlays for fade and local-time
  mapping.
"""

from __future__ import annotations

from typing import Callable

from svan2d.transition.pause.pause_descriptor import PauseDescriptor
from svan2d.transition.pause.pause_fraction_error import PauseFractionError


def build_pause_easing(
    pauses: list[PauseDescriptor],
    motion_speeds: list[float] | None = None,
) -> tuple[Callable[[float], float], list[tuple[float, float]]]:
    """Build the timeline easing and per-pause raw-time windows.

    Args:
        pauses: Pause descriptors, in arbitrary order.
        motion_speeds: Optional relative speeds for the *real* (nonzero-length)
            motion segments, in sorted-`at` order. With pauses at positions
            `0 < a_1 < ... < a_N < 1` there are N+1 motion segments
            (head, between..., tail); pauses at `at=0` or `at=1` collapse the
            adjacent edge segment, and that entry is omitted from
            `motion_speeds`. The motion input budget `M = 1 - Σ fractions` is
            distributed across the real segments in proportion to
            `speed_k * output_length_k`. Defaults to uniform velocity.

    Returns:
        `(easing, windows)`. `windows[i]` corresponds to `pauses[i]`.

    Raises:
        PauseFractionError: if `Σ fractions >= 1`.
        ValueError: if `motion_speeds` length does not match the number of
            real (nonzero-length) motion segments, or contains a non-positive
            value.
    """
    if not pauses:
        if motion_speeds is not None and len(motion_speeds) != 0:
            raise ValueError(
                f"motion_speeds length {len(motion_speeds)} must be 0 when "
                "there are no pauses"
            )
        return (lambda t: t, [])

    total = sum(p.fraction for p in pauses)
    if total >= 1.0:
        raise PauseFractionError([p.fraction for p in pauses])

    motion = 1.0 - total

    # Sort pauses by `at`, preserving original-index back-references so we can
    # return windows in input order.
    indexed = sorted(enumerate(pauses), key=lambda iv: iv[1].at)

    # Output lengths of the N+1 motion sub-segments (head, between..., tail).
    motion_out_lens: list[float] = []
    prev_at = 0.0
    for _, p in indexed:
        motion_out_lens.append(p.at - prev_at)
        prev_at = p.at
    motion_out_lens.append(1.0 - prev_at)

    n_segments = len(motion_out_lens)
    real_indices = [k for k, L in enumerate(motion_out_lens) if L > 0]
    expected = len(real_indices)
    if motion_speeds is None:
        speeds = [1.0] * n_segments
    else:
        if len(motion_speeds) != expected:
            raise ValueError(
                f"motion_speeds length {len(motion_speeds)} does not match "
                f"expected {expected} (number of nonzero-length motion segments)"
            )
        if any(s <= 0 for s in motion_speeds):
            raise ValueError(
                f"motion_speeds entries must be > 0, got {list(motion_speeds)}"
            )
        # Expand compact list to full N+1 entries; zero-length segments take 1.0
        # (their speed has no observable effect since their output length is 0).
        speeds = [1.0] * n_segments
        for slot, value in zip(real_indices, motion_speeds):
            speeds[slot] = float(value)

    weighted_total = sum(s * L for s, L in zip(speeds, motion_out_lens))

    def motion_in_len(k: int) -> float:
        if motion_out_lens[k] <= 0 or weighted_total <= 0:
            return 0.0
        return motion * speeds[k] * motion_out_lens[k] / weighted_total

    # Build piecewise segments: list of (in_start, in_end, out_start, out_end).
    segments: list[tuple[float, float, float, float]] = []
    windows_sorted: list[tuple[int, float, float]] = []

    in_cursor = 0.0
    out_cursor = 0.0

    for k, (orig_idx, p) in enumerate(indexed):
        m_out = motion_out_lens[k]
        if m_out > 0:
            m_in = motion_in_len(k)
            segments.append(
                (in_cursor, in_cursor + m_in, out_cursor, out_cursor + m_out)
            )
            in_cursor += m_in
            out_cursor += m_out

        pause_in_start = in_cursor
        pause_in_end = in_cursor + p.fraction
        segments.append((pause_in_start, pause_in_end, out_cursor, out_cursor))
        windows_sorted.append((orig_idx, pause_in_start, pause_in_end))
        in_cursor = pause_in_end

    tail_out = motion_out_lens[-1]
    if tail_out > 0:
        tail_in = motion_in_len(n_segments - 1)
        segments.append(
            (in_cursor, in_cursor + tail_in, out_cursor, out_cursor + tail_out)
        )

    # Reorder windows back to input order.
    windows = [(0.0, 0.0)] * len(pauses)
    for orig_idx, a, b in windows_sorted:
        windows[orig_idx] = (a, b)

    def easing(t: float) -> float:
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        for in_start, in_end, out_start, out_end in segments:
            if t <= in_end:
                if in_end == in_start:
                    return out_start
                local = (t - in_start) / (in_end - in_start)
                return out_start + local * (out_end - out_start)
        return 1.0

    return (easing, windows)
