from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.vscene import VScene
from svan2d.vscene.vscene_composite import VSceneComposite
from svan2d.vscene.vscene_exporter import VSceneExporter

from side_panel_scene import create_side_panel
from sieve import Sieve
from square_element import create_square_element
from utils import ring_to_total_number

from config import (
    COLOR_BACKGROUND,
    FRAME_RATE,
    GAP,
    NUM_RINGS,
    SQUARE_SIZE,
    TOTAL_FRAMES,
)

configure_logging(level="INFO")


def main():

    cell_size = SQUARE_SIZE + GAP
    scene_size = int(1.05 * (NUM_RINGS * 2 + 1) * cell_size)

    num = ring_to_total_number(NUM_RINGS)

    sieve = Sieve(num)
    sieve.run_all()

    num_steps = sieve.get_total_steps()
    step_stats = sieve.get_step_stats()

    step_time = 1 / num_steps

    report = sieve.get_full_report()

    elements = [
        create_square_element(i, report[i], step_time) for i in range(1, num + 1)
    ]

    animation_scene = VScene(
        width=scene_size,
        height=scene_size,
        background=COLOR_BACKGROUND,
    )

    animation_scene = animation_scene.add_elements(elements)

    # Scale factor to maintain consistent text size across different NUM_RINGS values
    reference_size = 2500
    scale_factor = scene_size / reference_size
    panel_width = int(scene_size * 0.4)

    side_panel_scene = create_side_panel(
        panel_width, scene_size, step_stats, scale_factor
    )

    comp = VSceneComposite([animation_scene, side_panel_scene], direction="horizontal")

    # Export
    exporter = VSceneExporter(
        comp,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="ulam_spiral_by_sieve",
        total_frames=TOTAL_FRAMES,
        framerate=FRAME_RATE,
        png_width_px=1024,
        parallel_workers=4,
        num_thumbnails=120,
    )


if __name__ == "__main__":
    main()
