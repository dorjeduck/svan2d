import math

from dataclasses import replace

from svan2d import (
    CircleState,
    Color,
    ConverterType,
    Point2D,
    VElement,
    VScene,
    VSceneExporter,
    configure_logging,
)
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
            pos=Point2D(250 * math.cos(rad), 250 * math.sin(rad)),
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

    def diagonal(t):
        if t < 0.5:
            return Point2D(100 - t * 200, 100 - t * 200)
        else:
            return Point2D(0)

    scene = automatic_camera(
        scene,
        offset=diagonal,
        padding=1.2,
        exclude=[ring],
    )

    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="53_automatic_camera_custom_offset_func",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
