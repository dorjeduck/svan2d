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
    c1 = CircleState(
        radius=20,
        pos=Point2D(-80, 0),
        fill_color=CIRCLE_COLOR,
    )
    c2 = replace(c1, pos=Point2D(-70, 0), radius=40)
    c3 = replace(c1, pos=Point2D(80, 0))

    s1 = SquareState(
        size=20,
        pos=Point2D(80, 0),
        fill_color=RECTANGLE_COLOR,
    )
    s2 = replace(s1, pos=Point2D(70, 0), size=50)
    s3 = replace(s1, pos=Point2D(-80, 0), size=20)

    # Swap position of the two components
    seg1, seg2 = segment.arc_swap_positions(
        state_1=c2,
        state_2=s2,
        t_start=0.3,
        t_end=0.7,
        arc_radius=70,
        clockwise=True,
        easing={"pos": easing.in_out_sine},
    )

    e1 = VElement().keystate(c1, at=0).segment(seg1).keystate(c3, at=1)
    e2 = VElement().keystate(s1, at=0).segment(seg2).keystate(s3, at=1)

    scene = scene.add_elements([e1, e2])

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="06_arc_swap_positions",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
