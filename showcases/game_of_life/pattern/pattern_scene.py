"""Create a scene for a single Game of Life pattern."""

from typing import Tuple

from svan2d.component.state import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement import VElement
from svan2d.vscene import VScene

from cell_element import create_cell_element
from config import (
    COLOR_BACKGROUND,
    GRID_MARGIN,
    SCENE_HEIGHT,
    SCENE_WIDTH,
    SHOW_DESCRIPTION,
    SHOW_PATTERN_NAME,
)
from life import create_empty_grid, next_generation
from patterns import Pattern


def get_pattern_bounds(pattern: Pattern) -> Tuple[int, int, int, int]:
    """Get bounding box of pattern: (min_x, min_y, max_x, max_y)."""
    xs = [c[0] for c in pattern.cells]
    ys = [c[1] for c in pattern.cells]
    return min(xs), min(ys), max(xs), max(ys)


def calculate_optimal_grid_size(pattern: Pattern) -> int:
    """Calculate optimal grid size by running simulation and tracking bounds.

    Pattern starts centered, so grid must accommodate max expansion in any direction.
    Adds margin so pattern doesn't reach the edge.
    """
    # Start with a large grid for simulation
    sim_size = 500
    grid = create_empty_grid(sim_size)

    # Place pattern in center
    min_x, min_y, max_x, max_y = get_pattern_bounds(pattern)
    pat_width = max_x - min_x + 1
    pat_height = max_y - min_y + 1
    offset_x = (sim_size - pat_width) // 2 - min_x
    offset_y = (sim_size - pat_height) // 2 - min_y

    # Calculate pattern center in sim grid
    center_x = sim_size // 2
    center_y = sim_size // 2

    for x, y in pattern.cells:
        gx, gy = offset_x + x, offset_y + y
        if 0 <= gx < sim_size and 0 <= gy < sim_size:
            grid[gy][gx] = True

    # Track max distance from center in any direction
    max_dist = 0

    for _ in range(pattern.generations):
        for y in range(sim_size):
            for x in range(sim_size):
                if grid[y][x]:
                    dist = max(abs(x - center_x), abs(y - center_y))
                    max_dist = max(max_dist, dist)
        grid = next_generation(grid)

    # Grid size = 2 * max_dist (to keep pattern centered) + margin
    size = 2 * max_dist + 1
    size_with_margin = int(size * (1 + GRID_MARGIN))

    return max(size_with_margin, 20)  # Minimum 20


def pattern_to_grid(pattern: Pattern, grid_size: int, offset: Tuple[int, int]) -> list:
    """Convert pattern cells to a grid."""
    grid = create_empty_grid(grid_size)
    ox, oy = offset
    for x, y in pattern.cells:
        gx, gy = ox + x, oy + y
        if 0 <= gx < grid_size and 0 <= gy < grid_size:
            grid[gy][gx] = True
    return grid


def run_simulation(grid: list, generations: int) -> list:
    """Run simulation and return history of all generations."""
    history = [grid]
    current = grid
    for _ in range(generations - 1):
        current = next_generation(current)
        history.append(current)
    return history


def create_pattern_scene(pattern: Pattern) -> VScene:
    """Create a VScene showing a single pattern evolution."""
    grid_size = pattern.grid_size or calculate_optimal_grid_size(pattern)

    # Center pattern in grid
    min_x, min_y, max_x, max_y = get_pattern_bounds(pattern)
    pat_width = max_x - min_x + 1
    pat_height = max_y - min_y + 1
    offset_x = (grid_size - pat_width) // 2 - min_x
    offset_y = (grid_size - pat_height) // 2 - min_y

    # Create grid and run simulation
    grid = pattern_to_grid(pattern, grid_size, (offset_x, offset_y))
    history = run_simulation(grid, pattern.generations)

    # Create scene
    scene = VScene(
        width=SCENE_WIDTH,
        height=SCENE_HEIGHT,
        background=COLOR_BACKGROUND,
    )

    # Add cells using shared cell_element module
    scene_size = min(SCENE_WIDTH, SCENE_HEIGHT)
    for y in range(grid_size):
        for x in range(grid_size):
            cell_history = [history[gen][y][x] for gen in range(pattern.generations)]
            element = create_cell_element(
                x, y, cell_history, grid_size, pattern.generations, scene_size
            )
            if element is not None:
                scene = scene.add_element(element)

    # Add pattern name text (keystates at 0 and 1 to persist)
    if SHOW_PATTERN_NAME:
        name_state = TextState(
            text=pattern.name,
            pos=Point2D(0, -SCENE_HEIGHT / 2 + 40),
            font_size=32,
            font_weight="bold",
            fill_color=Color("#FFFFFF"),
        )
        name_element = VElement().keystates([name_state, name_state])
        scene = scene.add_element(name_element)

    # Add description text
    if SHOW_DESCRIPTION:
        desc_state = TextState(
            text=pattern.description,
            pos=Point2D(0, -SCENE_HEIGHT / 2 + 70),
            font_size=18,
            fill_color=Color("#888888"),
        )
        desc_element = (
            VElement().keystate(desc_state, at=0.0).keystate(desc_state, at=1.0)
        )
        scene = scene.add_element(desc_element)

    return scene
