"""
Comprehensive showcase of all svan2d layout functions
Demonstrates each layout's unique characteristics with animated transition
"""

from svan2d.component import TextRenderer, TextState, Renderer
from svan2d.converter.converter_type import ConverterType
from svan2d.component.state import (
    ArcState,
    ArrowState,
    CircleState,
    CrossState,
    EllipseState,
    FlowerState,
    HeartState,
    InfinityState,
    LineState,
    PolygonState,
    RectangleState,
    SpiralState,
    SquareState,
    StarState,
    TriangleState,
    WaveState,
)
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.velement import VElement
from svan2d.velement.segments import fade_inout, hold
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from dataclasses import replace
from svan2d.core.color import Color

configure_logging(level="INFO")

FILL_COLOR = Color("#FDBE02")
STROKE_COLOR = Color("#AA0000")


def main():
    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    base_name_state = TextState(
        text="",
        font_family="Courier New",
        font_size=20,
        fill_color=Color("#AA0000"),
        pos=Point2D(0, 110),
    )

    # Define all layout transition
    morph_states = []
    morph_name_states = []

    morph_states.append(CircleState(fill_color=FILL_COLOR, stroke_color=STROKE_COLOR))
    morph_name_states.append(replace(base_name_state, text="Circle"))

    morph_states.append(
        ArrowState(fill_color=FILL_COLOR, stroke_color=STROKE_COLOR, rotation=-45),
    )
    morph_name_states.append(replace(base_name_state, text="Arrow"))

    morph_states.append(CrossState(fill_color=FILL_COLOR, stroke_color=STROKE_COLOR))
    morph_name_states.append(replace(base_name_state, text="Cross"))

    morph_states.append(
        LineState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Line"))

    morph_states.append(
        EllipseState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Ellipse"))

    morph_states.append(
        PolygonState(fill_color=FILL_COLOR, stroke_color=STROKE_COLOR, num_sides=5)
    )
    morph_name_states.append(replace(base_name_state, text="Pentagon"))

    morph_states.append(FlowerState(fill_color=FILL_COLOR, stroke_color=STROKE_COLOR))
    morph_name_states.append(replace(base_name_state, text="Flower"))

    morph_states.append(
        HeartState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Heart"))

    morph_states.append(
        WaveState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Wave"))

    morph_states.append(
        PolygonState(fill_color=FILL_COLOR, stroke_color=STROKE_COLOR, num_sides=6)
    )
    morph_name_states.append(replace(base_name_state, text="Hexagon"))

    morph_states.append(
        InfinityState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Infinity"))

    morph_states.append(
        PolygonState(fill_color=FILL_COLOR, stroke_color=STROKE_COLOR, num_sides=8)
    )

    morph_name_states.append(replace(base_name_state, text="Octagon"))

    morph_states.append(
        ArcState(
            stroke_color=STROKE_COLOR,
            radius=40,
            start_angle=10,
            end_angle=170,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Arc"))

    morph_states.append(
        RectangleState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Rectangle"))

    morph_states.append(
        PolygonState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Polygon"))

    morph_states.append(
        SpiralState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Spiral"))

    morph_states.append(
        SquareState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Square"))

    morph_states.append(
        StarState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Star"))

    morph_states.append(
        TriangleState(
            fill_color=FILL_COLOR,
            stroke_color=STROKE_COLOR,
        )
    )
    morph_name_states.append(replace(base_name_state, text="Triangle"))

    # Add all elements to the scene
    num_states = len(morph_states)

    hold_duration = 1 / (3 * num_states)
    fade_duration = 1 / (9 * num_states)

    morph_element = VElement().segment(
        hold(
            states=morph_states,
            duration=hold_duration,
        )
    )
    scene = scene.add_element(morph_element)

    texts = VElement().segment(
        fade_inout(
            morph_name_states,
            hold_duration=hold_duration,
            fade_duration=fade_duration,
        )
    )

    scene = scene.add_element(texts)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.CAIROSVG,
        output_dir="output/",
    )

    # Export to MP4 file
    exporter.to_mp4(
        filename="16_simple_morphs.mp4",
        total_frames=len(morph_states) * 30,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
