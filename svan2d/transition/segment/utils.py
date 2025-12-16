"""Utility functions for segment functions."""


def linspace(n: int, t1: float = 0.0, t2: float = 1.0) -> list[float]:
    """Generate n evenly spaced values from t1 to t2 (inclusive)."""
    if n == 1:
        return [(t1 + t2) / 2]

    dif = t2 - t1
    return [t1 + i * dif / (n - 1) for i in range(n)]
