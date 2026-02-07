"""Example: Crossfade between two elements.

Demonstrates using the crossfade segment function to fade
one element out while another fades in.
"""

from dataclasses import replace
from svan2d.component.state import CircleState, SquareState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.core.color import Color
from svan2d.velement import VElement
from svan2d.transition import segment
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

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
        converter=ConverterType.PLAYWRIGHT,
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
