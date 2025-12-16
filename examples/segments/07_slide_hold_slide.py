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

    states = []

    c1 = CircleState(
        radius=20,
        fill_color=CIRCLE_COLOR,
    )
    s1 = SquareState(
        size=40,
        fill_color=RECTANGLE_COLOR,
    )

    states.append(c1)
    states.append(s1)
    states.append(replace(c1, radius=30))
    states.append(replace(s1, size=50))

    segs = segment.slide_hold_slide(
        states,
        t_start=0,
        t_end=1,
        entrance_point=Point2D(70, 70),
        exit_point=Point2D(-70, -70),
        entrance_effect=segment.SlideEffect.FADE,
        exit_effect=segment.SlideEffect.FADE,
        slide_duration=1 / 10,
    )

    elements = [VElement().segment(seg) for seg in segs]

    scene.add_elements(elements)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="07_slide_hold_slide",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
