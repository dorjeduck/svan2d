from svan2d.animation.atomic import sequential_transition, trim
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
from svan2d.component.state.astroid import AstroidState
from svan2d.component.state.circle import CircleState
from svan2d.component.state.ellipse import EllipseState
from svan2d.component.state.polygon import PolygonState
from svan2d.component.state.ring import RingState

from svan2d.component.state.star import StarState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.velement import VElement
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
    s1 = CircleState(
        radius=200,
        clip_state=CircleState(radius=100),
        fill_color=FILL_COLOR,
        stroke_color=STROKE_COLOR,
        stroke_width=6,
    )

    s2 = CircleState(
        radius=270,
        clip_states=[
            CircleState(radius=50, y=-100),
            StarState(
                num_points_star=5, inner_radius=40, outer_radius=70, x=-120, y=60
            ),
            AstroidState(radius=100, num_cusps=4, curvature=0.3, x=100, y=60),
        ],
        fill_color=FILL_COLOR,
        stroke_color=STROKE_COLOR,
        stroke_width=6,
    )

    s3 = StarState(
        num_points_star=5,
        outer_radius=400,
        inner_radius=200,
        clip_states=[
            EllipseState(rx=50, ry=40, x=-70, y=-80),
            PolygonState(num_sides=3, size=80, x=40, y=40),
        ],
        fill_color=FILL_COLOR,
        stroke_color=STROKE_COLOR,
        stroke_width=6,
    )
    states = [s1, s2, s3, s2, s1]

    keystates = sequential_transition(states, trim, 0.5)

    element = VElement(renderer=VertexRenderer(), keystates=keystates)

    scene.add_element(element)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to PNG file
    exporter.to_mp4(
        filename="23_complex_morph_b.mp4",
        total_frames=240,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
