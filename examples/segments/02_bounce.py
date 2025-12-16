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
    circle = CircleState(
        radius=40,
        pos=Point2D(-50, 0),
        fill_color=CIRCLE_COLOR,
    )

    rectangle = SquareState(
        size=70,
        pos=Point2D(50, 0),
        fill_color=RECTANGLE_COLOR,
    )

    # bounce between circle and rectangle
    segs = segment.bounce(
        circle,
        rectangle,
        t_start=0.1,
        t_end=0.9,
        hold_duration=0.1,
        num_transitions=5,
    )

    bounce_element = (
        VElement().keystate(circle, at=0).segment(segs).keystate(rectangle, at=1)
    )
    scene.add_element(bounce_element)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="02_bounce",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
