from dataclasses import replace

from svan2d import (
    CircleState,
    Color,
    configure_logging,
    ConverterType,
    easing,
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

    # Create two different shapes
    s1 = CircleState(
        radius=40,
        fill_color=CIRCLE_COLOR,
    )

    s2 = SquareState(
        size=70,
        fill_color=RECTANGLE_COLOR,
    )

    # Crossfade from circle to rectangle
    segs = segment.fade_inout(
        states=[s1, s2],
        center_t=[0.3, 0.7],
        hold_duration=0.2,
        fade_duration=0.1,
        easing_dict={"opacity": easing.in_out_sine},
    )

    elements = [VElement().segment(seg) for seg in segs]
    scene = scene.add_elements(elements)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="04_fade_inout",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
