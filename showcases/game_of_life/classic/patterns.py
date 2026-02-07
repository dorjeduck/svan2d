"""Seed patterns for Conway's Game of Life."""

import random
from typing import List, Tuple

from life import Grid, create_empty_grid


def apply_pattern(grid: Grid, pattern: List[Tuple[int, int]], offset_x: int, offset_y: int) -> None:
    """Apply a pattern to the grid at the given offset."""
    size = len(grid)
    for dx, dy in pattern:
        x, y = offset_x + dx, offset_y + dy
        if 0 <= x < size and 0 <= y < size:
            grid[y][x] = True


def glider(grid: Grid, x: int, y: int) -> None:
    """Glider - moves diagonally."""
    pattern = [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)]
    apply_pattern(grid, pattern, x, y)


def blinker(grid: Grid, x: int, y: int) -> None:
    """Blinker - oscillator (period 2)."""
    pattern = [(0, 0), (1, 0), (2, 0)]
    apply_pattern(grid, pattern, x, y)


def beacon(grid: Grid, x: int, y: int) -> None:
    """Beacon - oscillator (period 2)."""
    pattern = [(0, 0), (1, 0), (0, 1), (3, 2), (2, 3), (3, 3)]
    apply_pattern(grid, pattern, x, y)


def toad(grid: Grid, x: int, y: int) -> None:
    """Toad - oscillator (period 2)."""
    pattern = [(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)]
    apply_pattern(grid, pattern, x, y)


def block(grid: Grid, x: int, y: int) -> None:
    """Block - still life."""
    pattern = [(0, 0), (1, 0), (0, 1), (1, 1)]
    apply_pattern(grid, pattern, x, y)


def beehive(grid: Grid, x: int, y: int) -> None:
    """Beehive - still life."""
    pattern = [(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (2, 2)]
    apply_pattern(grid, pattern, x, y)


def loaf(grid: Grid, x: int, y: int) -> None:
    """Loaf - still life."""
    pattern = [(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (3, 2), (2, 3)]
    apply_pattern(grid, pattern, x, y)


def pulsar(grid: Grid, x: int, y: int) -> None:
    """Pulsar - oscillator (period 3)."""
    pattern = [
        (2, 0), (3, 0), (4, 0), (8, 0), (9, 0), (10, 0),
        (0, 2), (5, 2), (7, 2), (12, 2),
        (0, 3), (5, 3), (7, 3), (12, 3),
        (0, 4), (5, 4), (7, 4), (12, 4),
        (2, 5), (3, 5), (4, 5), (8, 5), (9, 5), (10, 5),
        (2, 7), (3, 7), (4, 7), (8, 7), (9, 7), (10, 7),
        (0, 8), (5, 8), (7, 8), (12, 8),
        (0, 9), (5, 9), (7, 9), (12, 9),
        (0, 10), (5, 10), (7, 10), (12, 10),
        (2, 12), (3, 12), (4, 12), (8, 12), (9, 12), (10, 12),
    ]
    apply_pattern(grid, pattern, x, y)


def r_pentomino(grid: Grid, x: int, y: int) -> None:
    """R-pentomino - methuselah (long-lived chaos)."""
    pattern = [(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)]
    apply_pattern(grid, pattern, x, y)


def acorn(grid: Grid, x: int, y: int) -> None:
    """Acorn - methuselah that runs for 5206 generations."""
    pattern = [(1, 0), (3, 1), (0, 2), (1, 2), (4, 2), (5, 2), (6, 2)]
    apply_pattern(grid, pattern, x, y)


def lwss(grid: Grid, x: int, y: int) -> None:
    """Lightweight spaceship - moves horizontally."""
    pattern = [(1, 0), (4, 0), (0, 1), (0, 2), (4, 2), (0, 3), (1, 3), (2, 3), (3, 3)]
    apply_pattern(grid, pattern, x, y)


def random_fill(grid: Grid, density: float = 0.3) -> None:
    """Fill grid randomly with given density."""
    size = len(grid)
    for y in range(size):
        for x in range(size):
            if random.random() < density:
                grid[y][x] = True


def add_patterns(grid: Grid) -> None:
    """Add patterns at random positions, scaled by grid size."""
    size = len(grid)
    margin = 5

    def rand_pos(pattern_size: int = 5) -> Tuple[int, int]:
        """Get random position with margin for pattern."""
        max_pos = size - margin - pattern_size
        if max_pos < margin:
            max_pos = margin
        return random.randint(margin, max_pos), random.randint(margin, max_pos)

    # Pattern functions with their approximate sizes
    patterns_small = [
        (glider, 3),
        (blinker, 3),
        (block, 2),
        (beehive, 4),
    ]
    patterns_medium = [
        (beacon, 4),
        (toad, 4),
        (loaf, 4),
        (r_pentomino, 3),
        (lwss, 5),
    ]
    patterns_large = [
        (acorn, 7),
        (pulsar, 13),
    ]

    # Scale pattern count by grid size
    num_small = max(8, size // 3)
    num_medium = max(5, size // 5)
    num_large = max(2, size // 30)

    # Place small patterns
    for _ in range(num_small):
        pattern_func, pat_size = random.choice(patterns_small)
        pattern_func(grid, *rand_pos(pat_size))

    # Place medium patterns
    for _ in range(num_medium):
        pattern_func, pat_size = random.choice(patterns_medium)
        pattern_func(grid, *rand_pos(pat_size))

    # Place large patterns
    for _ in range(num_large):
        pattern_func, pat_size = random.choice(patterns_large)
        pattern_func(grid, *rand_pos(pat_size))


def create_initial_grid(size: int, mode: str = "mixed", density: float = 0.12) -> Grid:
    """Create initial grid based on mode.

    Args:
        size: Grid size
        mode: "mixed" (patterns + random), "random", "patterns"
        density: Random fill density for "random" and "mixed" modes
    """
    grid = create_empty_grid(size)

    if mode == "random":
        random_fill(grid, density)
    elif mode == "patterns":
        add_patterns(grid)
    else:  # mixed (default)
        random_fill(grid, density)
        add_patterns(grid)

    return grid
