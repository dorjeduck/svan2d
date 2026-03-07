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

    scene = scene.add_elements(elements)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
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
