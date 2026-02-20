"""Scalar interpolation and utility functions for transitions.

This module consolidates simple scalar operations:
- lerp: Linear interpolation
- angle: Angle interpolation with shortest-path wraparound
- step: Discrete step interpolation
- inbetween: Generate intermediate values
- circular_midpoint: Vector-averaged circular midpoint
- gaussian_smooth / gaussian_smooth_2d: Gaussian-smoothed function tracking
"""

import bisect
import math
from typing import Callable, List, Optional, TypeVar, Union

Number = Union[int, float]
T = TypeVar("T")


def lerp(start: Number, end: Number, t: float) -> float:
    """Linear interpolation between start and end values.

    Performs standard linear interpolation: lerp(a, b, t) = a + (b - a) * t

    Args:
        start: Starting value (int or float)
        end: Ending value (int or float)
        t: Interpolation parameter (0.0 to 1.0)
           - t=0.0 returns start
           - t=1.0 returns end
           - t=0.5 returns midpoint

    Returns:
        Interpolated value as float

    Examples:
        lerp(0, 100, 0.5)
        50.0
        lerp(10, 20, 0.25)
        12.5
        lerp(-10, 10, 0.75)
        5.0

    Note:
        Values of t outside [0, 1] are allowed and will extrapolate.
    """
    return start + (end - start) * t


def angle(start: Optional[float], end: Optional[float], t: float) -> float:
    """Interpolate between angles in degrees, taking the shortest path.

    This function handles angle wraparound to ensure smooth rotation along
    the shortest arc. For example, interpolating from 350° to 10° will
    go through 0° rather than backwards through 180°.

    Args:
        start: Starting angle in degrees (None is treated as 0.0)
        end: Ending angle in degrees (None is treated as 0.0)
        t: Interpolation parameter (0.0 to 1.0)
           - t=0.0 returns start angle
           - t=1.0 returns end angle
           - t=0.5 returns midpoint along shortest path

    Returns:
        Interpolated angle in degrees

    Examples:
        angle(0, 90, 0.5)
        45.0
        angle(350, 10, 0.5)  # Goes through 0°, not 180°
        0.0
        angle(None, 180, 1.0)  # None treated as 0
        180.0
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
    """Step interpolation with instant transition at midpoint.

    This is a discrete interpolation function that switches from start to end
    at t=0.5, with no gradual transition. Used for non-numeric values that
    cannot be smoothly interpolated (e.g., strings, enums, objects).

    Args:
        start: Starting value of any type
        end: Ending value of any type
        t: Interpolation parameter (0.0 to 1.0)
           - t < 0.5 returns start
           - t >= 0.5 returns end

    Returns:
        Either start or end value (no intermediate values)

    Examples:
        step("hello", "world", 0.3)
        'hello'
        step("hello", "world", 0.5)
        'world'
        step("hello", "world", 0.8)
        'world'
        step(True, False, 0.49)
        True

    Note:
        The transition happens exactly at t=0.5 (inclusive of end).
    """
    return start if t < 0.5 else end


def inbetween(start: Number, end: Number, num: int) -> List[float]:
    """Generate evenly-spaced values between start and end (exclusive).

    Creates a list of interpolated values between start and end, excluding
    the endpoints. Useful for generating intermediate animation frames or
    subdividing ranges.

    Args:
        start: Starting value (excluded from result)
        end: Ending value (excluded from result)
        num: Number of intermediate values to generate (must be >= 0)

    Returns:
        List of evenly-spaced float values between start and end

    Examples:
        inbetween(0, 10, 1)
        [5.0]
        inbetween(0, 10, 4)
        [2.0, 4.0, 6.0, 8.0]
        inbetween(0, 1, 3)
        [0.25, 0.5, 0.75]
        inbetween(0, 10, 0)
        []

    Note:
        To include endpoints, use numpy.linspace or manually add them:
        [start] + inbetween(start, end, num) + [end]
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
    """Calculate the midpoint between two angles on a circle.

    Uses vector averaging to find the true angular midpoint, which correctly
    handles cases where angles span across 0°/360°. This is geometrically
    correct for circular interpolation, unlike simple arithmetic mean.

    Args:
        a1: First angle in degrees (0-360)
        a2: Second angle in degrees (0-360)

    Returns:
        Midpoint angle in degrees (normalized to 0-360 range)

    Examples:
        circular_midpoint(0, 90)
        45.0
        circular_midpoint(350, 10)  # Spans 0°
        0.0
        circular_midpoint(270, 90)  # Opposite sides
        0.0

    Note:
        This differs from simple averaging: (350 + 10) / 2 = 180,
        but circular_midpoint(350, 10) = 0, which is geometrically correct.
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
