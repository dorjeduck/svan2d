from svan2d.core import (
    Color,
    Point2D,
    configure_logging,
)
from svan2d.converter import ConverterType
from svan2d.velement import VElement
from svan2d.vscene import (
    VScene,
    VSceneExporter,
)
from svan2d.primitive.state import CircleState
import math

from dataclasses import replace

from svan2d.vscene.automatic_camera import automatic_camera

configure_logging(level="INFO")

COLOR_ONE = Color("#FDBE02")
COLOR_TWO = Color("#AA0000")

NUM_CIRLCES = 6

def main():
    scene = VScene(width=600, height=600, background=Color("#000017"))

    colors = [
        COLOR_TWO.interpolate(COLOR_ONE, t / (NUM_CIRLCES - 1))
        for t in range(NUM_CIRLCES)
    ]

    step = 360 // NUM_CIRLCES
    angles = list(range(0, 360, step))

    circle_elements = []
    for i, (color, angle) in enumerate(zip(colors, angles)):
        rad = math.radians(angle)

        start = CircleState(
            radius=10,
            pos=Point2D(40 * math.cos(rad), 40 * math.sin(rad)),
            fill_color=Color(color),
        )
        d = 40 + 210 * i / (NUM_CIRLCES - 1)
        end = replace(
            start,
            pos=Point2D(d * math.cos(rad), d * math.sin(rad)),
        )

        circle_elements.append(VElement().keystates([start, end]))

    scene = scene.add_elements(circle_elements)

    ring = VElement(
        state=CircleState(
            radius=40,
            fill_color=Color.NONE,
            stroke_color=Color("#ffffff"),
            stroke_width=0.5,
            stroke_opacity=0.3,
        )
    )
    scene = scene.add_element(ring)

    scene = automatic_camera(scene, offset=Point2D(0, 0), padding=1.2, exclude=[ring])

    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="52_automatic_camera_custom_offset",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )

if __name__ == "__main__":
    main()
