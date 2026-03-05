"""Scalar interpolation and utility functions for transitions."""

import bisect
import math
from typing import Callable, TypeVar

Number = int | float
T = TypeVar("T")


def lerp(start: Number, end: Number, t: float) -> float:
    """Linear interpolation: ``start + (end - start) * t``. Extrapolates outside [0, 1]."""
    return start + (end - start) * t


def angle(start: float | None, end: float | None, t: float) -> float:
    """Interpolate between angles in degrees via the shortest arc.

    Handles wraparound so e.g. 350° → 10° passes through 0°, not 180°.
    ``None`` is treated as 0.0.
    """
    # Handle None values - treat as 0 degrees
    if start is None:
        start = 0.0
    if end is None:
        end = 0.0

    # Normalize angles to 0-360 range
    start = start % 360
    end = end % 360

    # Find the shortest direction
    diff = end - start
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360

    return start + diff * t


def step(start: T, end: T, t: float) -> T:
    """Discrete step: returns ``start`` for ``t < 0.5``, ``end`` for ``t >= 0.5``.

    Used for non-numeric values (strings, enums, booleans) that cannot be smoothly interpolated.
    """
    return start if t < 0.5 else end


def inbetween(start: Number, end: Number, num: int) -> list[float]:
    """Generate ``num`` evenly-spaced values strictly between start and end (endpoints excluded).

    Example: ``inbetween(0, 10, 4)`` → ``[2.0, 4.0, 6.0, 8.0]``
    """
    if num < 0:
        raise ValueError(f"num must be non-negative, got {num}")

    if num == 0:
        return []

    step_size = (end - start) / (num + 1)
    return [start + step_size * (i + 1) for i in range(num)]


def log_lerp(start: float, end: float, t: float) -> float:
    """Geometric (logarithmic) interpolation between two positive values.

    Equivalent to exp(lerp(log(start), log(end), t)). Produces smooth
    interpolation for values that change multiplicatively — such as
    stroke_width compensating for camera zoom, or scale factors.

    Falls back to linear interpolation if either value is <= 0.
    """
    if start <= 0 or end <= 0:
        return start + (end - start) * t
    return math.exp(math.log(start) * (1 - t) + math.log(end) * t)


def circular_midpoint(a1: float, a2: float) -> float:
    """Geometrically correct midpoint between two angles in degrees (0-360).

    Uses vector averaging, so it handles the 0°/360° wrap-around correctly.
    Example: ``circular_midpoint(350, 10)`` → ``0.0``, not ``180.0``.
    """
    # Convert degrees to radians
    a1_rad = math.radians(a1)
    a2_rad = math.radians(a2)

    # Convert to unit vectors
    x1, y1 = math.cos(a1_rad), math.sin(a1_rad)
    x2, y2 = math.cos(a2_rad), math.sin(a2_rad)

    # Average the vectors
    xm, ym = (x1 + x2) / 2, (y1 + y2) / 2

    # Compute the angle of the average vector
    mid_rad = math.atan2(ym, xm)
    mid_deg = math.degrees(mid_rad) % 360

    return mid_deg


def _gaussian_smooth(values: list[float], sigma_samples: float) -> list[float]:
    """Apply Gaussian smoothing to a list of sampled values."""
    n = len(values)
    if sigma_samples <= 0:
        return list(values)
    radius = int(math.ceil(3 * sigma_samples))
    kernel = [math.exp(-0.5 * (i / sigma_samples) ** 2) for i in range(-radius, radius + 1)]
    k_sum = sum(kernel)
    kernel = [k / k_sum for k in kernel]

    smoothed = []
    for i in range(n):
        val = 0.0
        for j, k in enumerate(kernel):
            idx = i + j - radius
            idx = max(0, min(n - 1, idx))
            val += values[idx] * k
        smoothed.append(val)
    return smoothed


def gaussian_smooth(
    func: Callable[[float], float],
    smoothness: float = 0.5,
    samples: int = 256,
    t_range: tuple[float, float] = (0.0, 1.0),
) -> Callable[[float], float]:
    """Gaussian-smooth a scalar function.

    Samples the function, applies Gaussian convolution, returns a callable
    that interpolates the smoothed values.

    Args:
        func: Target function to smooth.
        smoothness: 0.0 = no smoothing (original), 1.0 = heavy smoothing.
                    Controls Gaussian kernel width relative to t_range.
        samples: Number of sample points (higher = more accurate).
        t_range: Domain to sample over.
    """
    t_start, t_end = t_range
    dt = (t_end - t_start) / (samples - 1) if samples > 1 else 0.0
    ts = [t_start + i * dt for i in range(samples)]
    raw = [func(t) for t in ts]

    sigma_samples = smoothness * samples * 0.1
    smoothed = _gaussian_smooth(raw, sigma_samples)

    def interpolated(t: float) -> float:
        if t <= t_start:
            return smoothed[0]
        if t >= t_end:
            return smoothed[-1]
        idx = bisect.bisect_right(ts, t) - 1
        idx = max(0, min(samples - 2, idx))
        frac = (t - ts[idx]) / (ts[idx + 1] - ts[idx]) if ts[idx + 1] != ts[idx] else 0.0
        return smoothed[idx] + (smoothed[idx + 1] - smoothed[idx]) * frac

    return interpolated


def gaussian_smooth_2d(
    func: Callable[[float], tuple[float, float]],
    smoothness: float = 0.5,
    samples: int = 256,
    t_range: tuple[float, float] = (0.0, 1.0),
) -> Callable[[float], tuple[float, float]]:
    """Gaussian-smooth a 2D function. Same as gaussian_smooth but for (x, y).

    Smooths x and y channels independently.

    Args:
        func: Target function returning (x, y) to smooth.
        smoothness: 0.0 = no smoothing (original), 1.0 = heavy smoothing.
        samples: Number of sample points (higher = more accurate).
        t_range: Domain to sample over.
    """
    t_start, t_end = t_range
    dt = (t_end - t_start) / (samples - 1) if samples > 1 else 0.0
    ts = [t_start + i * dt for i in range(samples)]
    raw = [func(t) for t in ts]
    xs = [p[0] for p in raw]
    ys = [p[1] for p in raw]

    sigma_samples = smoothness * samples * 0.1
    sx = _gaussian_smooth(xs, sigma_samples)
    sy = _gaussian_smooth(ys, sigma_samples)

    def interpolated(t: float) -> tuple[float, float]:
        if t <= t_start:
            return (sx[0], sy[0])
        if t >= t_end:
            return (sx[-1], sy[-1])
        idx = bisect.bisect_right(ts, t) - 1
        idx = max(0, min(samples - 2, idx))
        frac = (t - ts[idx]) / (ts[idx + 1] - ts[idx]) if ts[idx + 1] != ts[idx] else 0.0
        x = sx[idx] + (sx[idx + 1] - sx[idx]) * frac
        y = sy[idx] + (sy[idx + 1] - sy[idx]) * frac
        return (x, y)

    return interpolated
