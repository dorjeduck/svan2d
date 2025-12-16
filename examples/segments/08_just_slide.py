from dataclasses import replace
from svan2d.component.state import CircleState, SquareState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.core.color import Color
from svan2d.transition import easing
from svan2d.transition.easing import easing2D
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
        radius=50,
        fill_color=CIRCLE_COLOR,
    )
    s1 = SquareState(
        size=70,
        fill_color=RECTANGLE_COLOR,
    )

    states.append(c1)
    states.append(s1)
    states.append(replace(c1, radius=40))
    states.append(replace(s1, size=60))
    states.append(c1)
    states.append(s1)

    segs = segment.just_slide(
        states,
        t_start=0,
        t_end=1,
        entrance_point=Point2D(100, -100),
        exit_point=Point2D(-100, 100),
        entrance_effect=segment.SlideEffect.FADE_SCALE,
        exit_effect=segment.SlideEffect.FADE_SCALE,
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
        filename="08_just_slide",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
