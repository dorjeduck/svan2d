"""Utility functions for segment functions."""


def linspace(n: int) -> list[float]:
    """Generate n evenly spaced values from 0.0 to 1.0."""
    if n == 1:
        return [0.0]
    return [i / (n - 1) for i in range(n)]
