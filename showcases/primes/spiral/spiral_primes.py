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
from svan2d.vscene.vscene_exporter import VSceneExporter

from square_element import create_square_element


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
    )

    xs = [i / (NUM_RINGS - 1) for i in range(NUM_RINGS)]
    ys = [get_scale_for_ring(i) for i in range(NUM_RINGS)]

    interp = PchipInterpolator(xs, ys)

    def scale_func(t: float) -> float:
        return float(interp(t))

    scene.animate_camera(
        scale=scale_func,
    )

    text_fade_out_start = min(1, RINGS_WITH_NUMBERS / NUM_RINGS)
    time_per_ring = 1 / NUM_RINGS

    number = 1

    for ring in range(NUM_RINGS):
        step = time_per_ring / max(8 * ring, 1)
        for n in range(max(8 * ring, 1)):
            appear_time = max((ring - 1) * time_per_ring + n * step, 0)

            square, text = create_square_element(
                number,
                appear_time,
                ring < RINGS_WITH_NUMBERS,
                text_fade_out_start,
            )

            scene.add_element(square)

            if text is not None:
                scene.add_element(text)

            number += 1

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.CAIROSVG,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="34_spiral_primes",
        total_frames=TOTAL_FRAMES,
        framerate=FRAME_RATE,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
