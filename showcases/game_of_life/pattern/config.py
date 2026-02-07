"""Configuration for Game of Life pattern showcase."""

from svan2d.core.color import Color

# Cell display
CELL_SIZE = 60  # Pixels per cell (used as max, scales down for large grids)
CELL_GAP = 2
GRID_MARGIN = 0.3  # Extra space around pattern (0.2 = 20%)

# Scene dimensions
SCENE_WIDTH = 1024
SCENE_HEIGHT = 768

# Animation timing (fraction of time between generations)
BIRTH_DURATION = 0.2  # Fraction of gen duration for birth
DEATH_DURATION = 0.5  # Fraction of gen duration for death

# Transition between patterns
TRANSITION_TYPE = "fade"  # "fade", "wipe", "slide", "zoom", "iris"
TRANSITION_FRAMES = 30  # Number of frames for transition

# Colors
COLOR_ALIVE = Color("#00D000")
COLOR_BACKGROUND = Color("#0f0f1a")
COLOR_DEATH = Color("#0f0f1a")  # Fades into background

# Text
SHOW_PATTERN_NAME = True
SHOW_DESCRIPTION = True

# Export
FPS = 60

# Patterns to include (True = include, False = skip)
PATTERNS_ENABLED = {
    # Simple Oscillators
    "Blinker": True,
    "Toad": True,
    "Beacon": True,
    "Clock": True,
    # Spaceships
    "Glider": True,
    "Lightweight Spaceship": True,
    "Middleweight Spaceship": True,
    "Heavyweight Spaceship": True,
    # Larger Oscillators
    "Figure Eight": True,
    "Kok's Galaxy": True,
    "Tumbler": True,
    "Pulsar": True,
    "Pentadecathlon": True,
    # Methuselahs
    "R-pentomino": True,
    "B-heptomino": True,
    "Pi-heptomino": True,
    "Diehard": True,
    "Acorn": True,
    # Advanced
    "Puffer Train": True,
    "Gosper Glider Gun": True,
}
