"""Spiral prime visualization with zoom-out effect.

Demonstrates:
- Ulam spiral pattern for positioning elements
- Staggered appearance animation using scale 0→1
- Scene-level camera animation for zoom-out (no wrapper groups needed!)
"""

from scipy.interpolate import PchipInterpolator

from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.transition import easing
from svan2d.vscene import VScene
from svan2d.vscene.vscene_composite import VSceneComposite
from svan2d.vscene.vscene_exporter import VSceneExporter

from side_panel_scene import create_side_panel
from square_element import create_square_element
from utils import is_prime


from config import (
    COLOR_BACKGROUND,
    FRAME_RATE,
    GAP,
    NUM_RINGS,
    RINGS_WITH_NUMBERS,
    SCENE_SIZE,
    SQUARE_SIZE,
    TOTAL_FRAMES,
)

configure_logging(level="INFO")


def main():

    cell_size = SQUARE_SIZE + GAP
    view_size = SCENE_SIZE * 0.95

    def get_scale_for_ring(ring: int) -> float:
        extent = (2 * ring + 3) * cell_size
        return view_size / extent

    scene = VScene(
        width=SCENE_SIZE,
        height=SCENE_SIZE,
        background=COLOR_BACKGROUND,
        timeline_easing=easing.in_sine,
    )

    xs = [i / (NUM_RINGS - 1) for i in range(NUM_RINGS)]
    ys = [get_scale_for_ring(i) for i in range(NUM_RINGS)]

    interp = PchipInterpolator(xs, ys)

    def scale_func(t: float) -> float:
        return float(interp(t))

    scene = scene.animate_camera(
        scale=scale_func,
    )

    text_fade_out_start = min(1, (RINGS_WITH_NUMBERS + 1) / NUM_RINGS)
    time_per_ring = 1 / NUM_RINGS

    number = 1
    fade_duration = time_per_ring

    # Track stats for side panel
    # Initial state at t=0: only number 1 visible, no primes/composites yet
    step_stats = [
        {
            "step": 1,
            "num_primes": 0,
            "num_composites": 0,
            "appear_time": 0.0,
        }
    ]
    num_primes = 0
    num_composites = 0

    for round in range(NUM_RINGS + 1):
        step = time_per_ring / max(8 * round, 1)
        for n in range(max(8 * round, 1)):
            appear_time = max((round - 1) * time_per_ring + n * step, 0)

            square, text = create_square_element(
                number,
                appear_time,
                fade_duration,
                round <= RINGS_WITH_NUMBERS,
                text_fade_out_start,
            )

            scene = scene.add_element(square)

            if text is not None:
                scene = scene.add_element(text)

            # Track stats for numbers >= 2
            if number >= 2:
                if is_prime(number):
                    num_primes += 1
                else:
                    num_composites += 1

                step_stats.append(
                    {
                        "step": number,
                        "num_primes": num_primes,
                        "num_composites": num_composites,
                        "appear_time": min(1, appear_time + step),
                    }
                )

            number += 1

    # Create side panel
    # Scale factor to maintain consistent text size across different SCENE_SIZE values
    reference_size = 2500
    scale_factor = SCENE_SIZE / reference_size
    panel_width = int(SCENE_SIZE * 0.4)

    side_panel = create_side_panel(
        panel_width, SCENE_SIZE, easing.in_sine, step_stats, scale_factor
    )

    # Combine animation and side panel
    composite = VSceneComposite([scene, side_panel], direction="horizontal")

    # Export
    exporter = VSceneExporter(
        scene=composite,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="ulam_spiral_by_steps",
        total_frames=TOTAL_FRAMES,
        framerate=FRAME_RATE,
        png_width_px=1024,
        num_thumbnails=20,
        parallel_workers=4,
    )


if __name__ == "__main__":
    main()
