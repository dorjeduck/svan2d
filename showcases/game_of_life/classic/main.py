"""Conway's Game of Life animated showcase.

Demonstrates:
- Grid layout with animated cells
- Scale animations for birth/death
- Color transitions
- Game of Life simulation
"""

from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

from cell_element import create_cell_element
from config import (
    COLOR_BACKGROUND,
    FPS,
    GENERATIONS,
    GRID_SIZE,
    INIT_MODE,
    RANDOM_DENSITY,
    SCENE_SIZE,
    TOTAL_FRAMES,
)
from life import run_simulation
from patterns import create_initial_grid

configure_logging(level="INFO")


def main():
    # Initialize grid
    initial_grid = create_initial_grid(
        GRID_SIZE, mode=INIT_MODE, density=RANDOM_DENSITY
    )

    # Run simulation
    history = run_simulation(initial_grid, GENERATIONS)

    # Create scene
    scene = VScene(
        width=SCENE_SIZE,
        height=SCENE_SIZE,
        background=COLOR_BACKGROUND,
    )

    # Create cell elements with animation based on history
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            # Get life history for this cell
            cell_history = [history[gen][y][x] for gen in range(GENERATIONS)]

            element = create_cell_element(x, y, cell_history, GRID_SIZE)
            if element is not None:
                scene = scene.add_element(element)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="game_of_life",
        total_frames=TOTAL_FRAMES,
        framerate=FPS,
        png_width_px=800,
        num_thumbnails=100,
        parallel_workers=4,
    )


if __name__ == "__main__":
    main()
