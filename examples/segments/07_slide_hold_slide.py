from dataclasses import replace

from svan2d import (
    CircleState,
    Color,
    configure_logging,
    ConverterType,
    Point2D,
    SquareState,
    VElement,
    VScene,
    VSceneExporter,
)
from svan2d.transition import segment

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
        entrance_point=Point2D(70, -70),
        exit_point=Point2D(-70, 70),
        entrance_effect=segment.SlideEffect.FADE,
        exit_effect=segment.SlideEffect.FADE,
        slide_duration=1 / 10,
    )

    elements = [VElement().segment(seg) for seg in segs]  # type: ignore

    scene = scene.add_elements(elements)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="07_slide_hold_slide",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
