"""Parametric shape definitions for Fourier epicycles showcase.

Each function returns a list of complex numbers sampling the shape path.
"""

from __future__ import annotations

import math
from typing import Callable

ShapeFunc = Callable[..., list[complex]]


def heart(num_samples: int, scale: float) -> list[complex]:
    """Heart curve using the same parametric formula as HeartState."""
    points = []
    for i in range(num_samples):
        t = (i / num_samples) * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = -(
            13 * math.cos(t)
            - 5 * math.cos(2 * t)
            - 2 * math.cos(3 * t)
            - math.cos(4 * t)
        )
        points.append(complex(x * scale / 20, y * scale / 20))
    return points


def star(
    num_samples: int,
    scale: float,
    num_points: int = 5,
    inner_ratio: float = 0.4,
) -> list[complex]:
    """Star shape with alternating outer/inner radii."""
    corners = []
    for i in range(num_points * 2):
        angle = math.pi / 2 + i * math.pi / num_points
        r = scale if i % 2 == 0 else scale * inner_ratio
        corners.append(complex(r * math.cos(angle), r * math.sin(angle)))
    return _resample_path(corners, num_samples)


def circle_shape(num_samples: int, scale: float) -> list[complex]:
    """Simple circle."""
    return [
        complex(
            scale * math.cos(2 * math.pi * i / num_samples),
            scale * math.sin(2 * math.pi * i / num_samples),
        )
        for i in range(num_samples)
    ]


def square(num_samples: int, scale: float) -> list[complex]:
    """Square path."""
    corners = [
        complex(-scale, -scale),
        complex(scale, -scale),
        complex(scale, scale),
        complex(-scale, scale),
    ]
    return _resample_path(corners, num_samples)


def infinity(num_samples: int, scale: float) -> list[complex]:
    """Lemniscate of Bernoulli (same formula as InfinityState)."""
    points = []
    for i in range(num_samples):
        t = (i / num_samples) * 2 * math.pi
        denom = 1 + math.sin(t) ** 2
        x = scale * math.cos(t) / denom
        y = scale * math.sin(t) * math.cos(t) / denom
        points.append(complex(x, y))
    return points


def _resample_path(vertices: list[complex], num_samples: int) -> list[complex]:
    """Evenly resample a closed polyline to num_samples points."""
    n = len(vertices)
    # Compute cumulative arc lengths along the closed polygon
    lengths = [0.0]
    for i in range(n):
        seg = abs(vertices[(i + 1) % n] - vertices[i])
        lengths.append(lengths[-1] + seg)
    total = lengths[-1]

    result = []
    for i in range(num_samples):
        target = total * i / num_samples
        # Find which segment this falls in
        for j in range(n):
            if lengths[j + 1] >= target:
                seg_start = lengths[j]
                seg_len = lengths[j + 1] - lengths[j]
                if seg_len < 1e-12:
                    frac = 0.0
                else:
                    frac = (target - seg_start) / seg_len
                a = vertices[j]
                b = vertices[(j + 1) % n]
                result.append(a + (b - a) * frac)
                break
    return result


SHAPES: dict[str, ShapeFunc] = {
    "heart": heart,
    "star": star,
    "circle": circle_shape,
    "square": square,
    "infinity": infinity,
}


def get_shape(name: str, num_samples: int, scale: float) -> list[complex]:
    """Look up a shape by name and return sampled points."""
    if name not in SHAPES:
        raise ValueError(f"Unknown shape '{name}'. Available: {list(SHAPES.keys())}")
    return SHAPES[name](num_samples, scale)
