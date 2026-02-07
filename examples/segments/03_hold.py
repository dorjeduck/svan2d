from dataclasses import replace
from svan2d.component.state import CircleState, SquareState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.core.color import Color
from svan2d.velement import VElement
from svan2d.transition import easing, segment
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

configure_logging(level="INFO")

CIRCLE_COLOR = Color("#FDBE02")
RECTANGLE_COLOR = Color("#AA0000")

NUM_OF_EACH = 2
X_RANGE = 100


def main():
    scene = VScene(width=256, height=256, background=Color("#000017"))

    start = -X_RANGE / 2
    step = X_RANGE / (NUM_OF_EACH * 2 - 1)

    states = []
    for i in range(NUM_OF_EACH):

        states.append(
            CircleState(
                radius=40,
                pos=Point2D(start + i * 2 * step, 0),
                fill_color=CIRCLE_COLOR,
            )
        )

        states.append(
            SquareState(
                size=70,
                pos=Point2D(start + (i * 2 + 1) * step, 0),
                fill_color=RECTANGLE_COLOR,
            )
        )

    start = replace(states[0], pos=states[0].pos - Point2D(40, 0), radius=20)
    end = replace(states[-1], pos=states[-1].pos + Point2D(40, 0), size=40)

    # hold at each key state for a short bit
    segs = segment.hold(
        states=states,
        at=segment.linspace(2 * NUM_OF_EACH + 2)[1:-1],
        hold_duration=1 / (6 * NUM_OF_EACH),
        easing_dict={"pos": easing.in_out_sine},
    )

    hold_element = VElement().keystate(start, at=0).segment(segs).keystate(end, at=1)

    scene = scene.add_element(hold_element)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="03_hold",
        total_frames=120,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
