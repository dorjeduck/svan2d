"""Configuration for Conway's Game of Life showcase."""

from svan2d.core.color import Color

# Grid settings
GRID_SIZE = 50  # 30x30 grid (900 cells)
CELL_SIZE = 90  # Pixels
CELL_GAP = 2  # Spacing between cells

# Simulation settings
GENERATIONS = 100  # Number of simulation steps
FRAMES_PER_GEN = 10  # Animation frames per generation
BIRTH_DURATION = 0.2  # Generations for birth animation (scale/opacity 0→1)
DEATH_DURATION = 0.5  # Generations for death animation (scale/opacity 1→0)

# Initial pattern mode: "patterns" (default), "random", "mixed"
INIT_MODE = "patterns"
RANDOM_DENSITY = 0.2  # For "random" and "mixed" modes

# Colors
COLOR_ALIVE = Color("#00D000")
COLOR_BACKGROUND = Color("#0f0f1a")
COLOR_DEATH = Color("#0f0f1a")  # fades into background

# Export settings
TOTAL_FRAMES = GENERATIONS * FRAMES_PER_GEN
FPS = 90

# Scene dimensions (calculated from grid)
SCENE_SIZE = GRID_SIZE * (CELL_SIZE + CELL_GAP) + 40  # Add margin
