from svan2d.component.state import CircleState, SquareState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.core.color import Color
from svan2d.transition import easing
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

configure_logging(level="INFO")

CIRCLE_COLOR = Color("#FDBE02")
RECTANGLE_COLOR = Color("#AA0000")


def main():
    scene = VScene(width=256, height=256, background=Color("#000017"))

    # Create two different shapes
    circle = CircleState(
        radius=20,
        pos=Point2D(-90, -90),
        fill_color=CIRCLE_COLOR,
    )

    square = SquareState(
        size=40,
        pos=Point2D(90, 90),
        fill_color=RECTANGLE_COLOR,
    )

    easing_overrides = [
        easing.linear,
        easing.in_cubic,
        easing.in_expo,
        easing.in_out_cubic,
        easing.in_out_bounce,
    ]

    step = 1 / (2 * len(easing_overrides))

    vel = VElement()

    for i, eas in enumerate(easing_overrides):

        vel = vel.keystate(
            circle,
            at=2 * i * step,
        ).transition(
            easing_dict={
                "pos": easing.easing2D(
                    easing_x=easing.linear,
                    easing_y=eas,
                )
            }
        ).keystate(
            square,
            at=min(1, (2 * i + 1) * step),
        ).transition(
            easing_dict={
                "pos": easing.easing2D(
                    easing_x=easing.linear,
                    easing_y=eas,
                )
            }
        )
    vel = vel.keystate(circle, at=1)

    scene = scene.add_element(vel)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="23_easing2D",
        total_frames=480,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
