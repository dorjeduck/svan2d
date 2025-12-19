"""Example: M->N shape group morphing using ShapeCollectionState

Demonstrates morphing between different numbers of independent shapes:
- 3 triangles + 2 squares -> 1 ellipse + 3 rectangles

Each shape has independent colors and properties. The mapping uses
Mapper strategies (GreedyMapper by default).
"""

from svan2d.component.state import (
    StateCollectionState,
    TriangleState,
    SquareState,
    EllipseState,
    RectangleState,
)
from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.core.color import Color

configure_logging(level="INFO")


def main():
    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    state1 = StateCollectionState(
        states=[
            TriangleState(
                pos=Point2D(-70, -50),
                size=30,
                fill_color=Color("#F3B700"),
                
            ),
            TriangleState(
                pos=Point2D(0, -50),
                size=30,
                fill_color=Color("#FAA300"),
                
            ),
            TriangleState(
                pos=Point2D(70, -50),
                size=30,
                fill_color=Color("#E57C04"),
               
            ),
            SquareState(
                pos=Point2D(-50, 50),
                size=40,
                fill_color=Color("#F63E02"),
                
            ),
            SquareState(
                pos=Point2D(50, 50),
                size=40,
                fill_color=Color("#FF0000"),
               
            ),
        ]
    )

    state2 = StateCollectionState(
        states=[
            EllipseState(
                pos=Point2D(0, -60),
                rx=70,
                ry=30,
                fill_color=Color("#FDBE02"),
                
            ),
            RectangleState(
                pos=Point2D(70, 50),
                width=50,
                height=30,
                fill_color=Color("#FDBE02"),
                
            ),
        ]
    )

    # Create element with morphing animation
    element = (
        VElement()
        .keystate(state1, at=0.0)
        .keystate(state2, at=0.5)
        .keystate(state1, at=1.0)
    )

    scene.add_element(element)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to MP4
    exporter.to_mp4(
        filename="24_state_collection_morphing",
        total_frames=180,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
