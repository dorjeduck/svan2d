from dataclasses import replace
from svan2d.component.state import (
    StateCollectionState,
    TriangleState,
    SquareState,
)
from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.velement import VElement
from svan2d.transition.segment import hold
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.core.color import Color

configure_logging(level="INFO")


def main():
    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    states = [
        TriangleState(
            pos=Point2D(-70, -50),
            size=30,
            fill_color=Color("#F3B700"),
            scale=0,
        ),
        TriangleState(
            pos=Point2D(0, -50),
            size=30,
            fill_color=Color("#FAA300"),
            scale=0,
        ),
        TriangleState(
            pos=Point2D(70, -50),
            size=30,
            fill_color=Color("#E57C04"),
            scale=0,
        ),
        SquareState(
            pos=Point2D(-50, 50),
            size=40,
            fill_color=Color("#F63E02"),
            scale=0,
        ),
        SquareState(
            pos=Point2D(50, 50),
            size=40,
            fill_color=Color("#FF0000"),
            scale=0,
        ),
    ]

    morph_states = [replace(state, scale=1) for state in states]

    collection_1 = StateCollectionState(states=morph_states[:3])
    collection_2 = StateCollectionState(states=morph_states[3:])

    # Create animation

    # 1 fade in

    start_elements = [
        VElement().keystate(s1, at=0).keystate(s2, at=0.2)
        for s1, s2 in zip(
            states[:3],
            morph_states[:3],
        )
    ]

    scene = scene.add_elements(start_elements)

    # 2. Morph
    morph_element = (
        VElement().keystate(collection_1, at=0.2).keystate(collection_2, at=0.8)
    )

    scene = scene.add_element(morph_element)

    # fade out

    end_elements = [
        VElement().keystate(s1, at=0.8).keystate(s2, at=1)
        for s1, s2 in zip(
            morph_states[3:],
            states[3:],
        )
    ]

    scene = scene.add_elements(end_elements)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to MP4
    exporter.to_mp4(
        filename="25_embedded_state_collection_morphing",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
