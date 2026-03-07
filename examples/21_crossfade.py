"""Example: Crossfade between two elements.

Demonstrates using the crossfade segment function to fade
one element out while another fades in.
"""

from dataclasses import replace

from svan2d import (
    CircleState,
    Color,
    configure_logging,
    ConverterType,
    Point2D,
    SquareState,
    VElement,
    VScene,
    VSceneExporter,
)
from svan2d.transition import segment

configure_logging(level="INFO")

CIRCLE_COLOR = Color("#FDBE02")
RECTANGLE_COLOR = Color("#AA0000")


def main():
    scene = VScene(width=256, height=256, background=Color("#000017"))

    # Create two different shapes
    c1 = CircleState(
        radius=20,
        pos=Point2D(-90, 0),
        fill_color=CIRCLE_COLOR,
    )
    c2 = replace(c1, radius=60, pos=Point2D(0, 0))

    r1 = SquareState(
        size=100,
        pos=Point2D(0, 0),
        fill_color=RECTANGLE_COLOR,
    )
    r2 = replace(r1, size=20, pos=Point2D(90, 0))

    # Crossfade from circle to rectangle
    circle_out, rectangle_in = segment.crossfade(c2, r1, t_start=0.3, t_end=0.7)

    elem_circle = VElement().keystate(c1, at=0).segment(circle_out)
    elem_rectangle = VElement().segment(rectangle_in).keystate(r2, at=1)

    scene = scene.add_elements([elem_circle, elem_rectangle])

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="21_crossfade",
        total_frames=60,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
