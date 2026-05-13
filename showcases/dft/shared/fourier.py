"""Discrete Fourier Transform computation for epicycle animation."""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FourierCoefficient:
    """A single Fourier coefficient describing one epicycle."""

    freq: int
    radius: float
    phase: float


def compute_dft(samples: list[complex]) -> list[FourierCoefficient]:
    """Compute the DFT of complex samples, sorted by radius descending.

    Args:
        samples: Complex path samples (evenly spaced in parameter space).

    Returns:
        List of FourierCoefficient sorted by radius (largest first).
    """
    n = len(samples)
    coefficients = []
    for k in range(n):
        total = complex(0, 0)
        for j in range(n):
            angle = -2 * math.pi * k * j / n
            total += samples[j] * cmath.exp(complex(0, angle))
        total /= n
        # Center frequencies: k > N/2 wraps to negative frequency (k - N).
        # This ensures freq 199 in a 200-sample DFT is treated as freq -1
        # (one slow reverse rotation) instead of 199 fast forward rotations.
        freq = k if k <= n // 2 else k - n
        coefficients.append(
            FourierCoefficient(
                freq=freq,
                radius=abs(total),
                phase=cmath.phase(total),
            )
        )
    # Sort by radius descending so largest circles come first
    coefficients.sort(key=lambda c: c.radius, reverse=True)
    return coefficients


def evaluate_epicycles(
    coefficients: list[FourierCoefficient], t: float, max_index: int | None = None
) -> list[complex]:
    """Evaluate the cumulative epicycle chain at time t.

    Args:
        coefficients: Fourier coefficients (sorted by radius descending).
        t: Time parameter in [0, 1) representing one full cycle.
        max_index: Optional maximum position index to compute (stops early for performance).

    Returns:
        List of cumulative positions along the chain.
        positions[0] is the center of the first (largest) circle,
        positions[-1] is the tip (drawing point) or last requested position.
    """
    positions = [complex(0, 0)]
    limit = len(coefficients) if max_index is None else min(max_index, len(coefficients))
    for i, c in enumerate(coefficients):
        if i >= limit:
            break
        angle = 2 * math.pi * c.freq * t + c.phase
        offset = c.radius * cmath.exp(complex(0, angle))
        positions.append(positions[-1] + offset)
    return positions


def evaluate_tip(coefficients: list[FourierCoefficient], t: float) -> complex:
    """Evaluate just the tip position (sum of all epicycles) at time t."""
    total = complex(0, 0)
    for c in coefficients:
        angle = 2 * math.pi * c.freq * t + c.phase
        total += c.radius * cmath.exp(complex(0, angle))
    return total


def evaluate_shape_loop(
    coefficients: list[FourierCoefficient], num_points: int
) -> list[complex]:
    """Evaluate the complete closed shape as num_points vertices."""
    return [evaluate_tip(coefficients, i / num_points) for i in range(num_points)]


def interpolate_coefficients(
    coeffs_a: list[FourierCoefficient],
    coeffs_b: list[FourierCoefficient],
    t: float,
) -> list[FourierCoefficient]:
    """Interpolate between two coefficient sets matched by frequency.

    Missing frequencies in either set are treated as zero amplitude.
    """
    map_a = {c.freq: c for c in coeffs_a}
    map_b = {c.freq: c for c in coeffs_b}
    all_freqs = sorted(set(map_a) | set(map_b), key=abs)

    result = []
    for freq in all_freqs:
        a = map_a.get(freq)
        b = map_b.get(freq)
        ca = a.radius * cmath.exp(complex(0, a.phase)) if a else 0
        cb = b.radius * cmath.exp(complex(0, b.phase)) if b else 0
        c_interp = ca * (1 - t) + cb * t
        result.append(
            FourierCoefficient(
                freq=freq,
                radius=abs(c_interp),
                phase=cmath.phase(c_interp),
            )
        )
    return result


def filter_coefficients(
    coefficients: list[FourierCoefficient], max_abs_freq: int
) -> tuple[list[FourierCoefficient], list[FourierCoefficient]]:
    """Split coefficients into kept (|freq| <= cutoff) and removed.

    Returns:
        (kept, removed) tuple of coefficient lists.
    """
    kept = [c for c in coefficients if abs(c.freq) <= max_abs_freq]
    removed = [c for c in coefficients if abs(c.freq) > max_abs_freq]
    return kept, removed
