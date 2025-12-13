from svan2d.component.renderer.base_vertex import VertexRenderer
from svan2d.component.state import (
    PerforatedCircleState,
    PerforatedStarState,
    Astroid,
    Star,
    Ellipse,
    Polygon,
    Circle,
)
from svan2d.component.state.ring import RingState

from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.velement import VElement
from svan2d.velement.segments import hold
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.core.color import Color

configure_logging(level="INFO")

FILL_COLOR = Color("#FDBE02")
STROKE_COLOR = Color("#AA0000")


def main():

    # Create the scene
    scene = VScene(width=1024, height=1024, background=Color("#000017"))

    # equivalent to a Ring but the stroke around the hole which is present here
    # can smoothly morph into vertex loops without surrounding strokes
    s1 = PerforatedCircleState(
        radius=200,
        holes=[Circle(radius=100)],
        fill_color=FILL_COLOR,
        stroke_color=STROKE_COLOR,
        stroke_width=6,
    )

    s2 = PerforatedCircleState(
        radius=270,
        holes=[
            Circle(radius=50, pos=Point2D(0, -100)),
            Star(num_points=5, inner_radius=40, outer_radius=70, pos=Point2D(-120, 60)),
            Astroid(radius=100, num_cusps=4, curvature=0.3, pos=Point2D(100, 60)),
        ],
        fill_color=FILL_COLOR,
        stroke_color=STROKE_COLOR,
        stroke_width=6,
        holes_stroke_width=0,
    )

    s3 = PerforatedStarState(
        num_points=5,
        outer_radius=400,
        inner_radius=200,
        holes=[
            Ellipse(rx=50, ry=40, pos=Point2D(-70, -80)),
            Polygon(num_sides=3, radius=80, pos=Point2D(40, 40)),
        ],
        fill_color=FILL_COLOR,
        stroke_color=STROKE_COLOR,
        stroke_width=6,
        holes_stroke_width=0,
    )
    states = [s1, s2, s3, s2, s1]

    element = VElement(renderer=VertexRenderer()).segment(
        hold(states=states, duration=1.0 / (3 * len(states)))
    )

    scene.add_element(element)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to PNG file
    exporter.to_mp4(
        filename="17_complex_morph.mp4",
        total_frames=240,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
