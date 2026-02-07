"""Conway's Game of Life logic."""

from typing import List

Grid = List[List[bool]]


def create_empty_grid(size: int) -> Grid:
    """Create an empty grid of given size."""
    return [[False for _ in range(size)] for _ in range(size)]


def count_neighbors(grid: Grid, x: int, y: int) -> int:
    """Count live neighbors for cell at (x, y)."""
    size = len(grid)
    count = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < size and 0 <= ny < size:
                if grid[ny][nx]:
                    count += 1
    return count


def next_generation(grid: Grid) -> Grid:
    """Compute the next generation according to Game of Life rules.

    Rules:
    - Live cell with 2-3 neighbors survives
    - Dead cell with exactly 3 neighbors becomes alive
    - All other cells die or stay dead
    """
    size = len(grid)
    new_grid = create_empty_grid(size)

    for y in range(size):
        for x in range(size):
            neighbors = count_neighbors(grid, x, y)
            if grid[y][x]:
                # Live cell survives with 2-3 neighbors
                new_grid[y][x] = neighbors in (2, 3)
            else:
                # Dead cell becomes alive with exactly 3 neighbors
                new_grid[y][x] = neighbors == 3

    return new_grid


def run_simulation(initial_grid: Grid, generations: int) -> List[Grid]:
    """Run simulation and return list of all generations."""
    history = [initial_grid]
    current = initial_grid

    for _ in range(generations - 1):
        current = next_generation(current)
        history.append(current)

    return history
