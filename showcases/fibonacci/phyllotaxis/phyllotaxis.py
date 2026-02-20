"""Pure math for the phyllotaxis (sunflower) pattern.

Vogel's model: seed n is placed at angle n * golden_angle,
distance c * sqrt(n) from center.
"""

import math

GOLDEN_ANGLE_DEG = 137.50776405003785
GOLDEN_ANGLE_RAD = math.radians(GOLDEN_ANGLE_DEG)


def seed_position(n: int, c: float) -> tuple[float, float]:
    """Compute (x, y) for seed n using Vogel's model.

    Args:
        n: Seed index (0-based).
        c: Spacing constant controlling density.

    Returns:
        (x, y) position.
    """
    angle = n * GOLDEN_ANGLE_RAD
    r = c * math.sqrt(n)
    return (r * math.cos(angle), r * math.sin(angle))


def fibonacci(index: int) -> int:
    """Return the Fibonacci number at the given 1-based index.

    1→1, 2→1, 3→2, 4→3, 5→5, 6→8, 7→13, 8→21, ...
    """
    a, b = 0, 1
    for _ in range(index):
        a, b = b, a + b
    return a


def spiral_family(n: int, num_spirals: int) -> int:
    """Return which spiral family (0..num_spirals-1) seed n belongs to.

    Seeds sharing the same family index visually form one of the
    num_spirals spirals (typically a Fibonacci number like 13 or 21).
    """
    return n % num_spirals
