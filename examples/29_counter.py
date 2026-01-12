from dataclasses import replace
from svan2d.component.state.number import NumberFormat, NumberState
from svan2d.component.state.rectangle import RectangleState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.point2d import Point2D
from svan2d.core.logger import configure_logging
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.core.color import Color


configure_logging(level="INFO")

FROM = 1
TO = 120


COUNTER_COLOR = Color("#FDBE02")
BAR_COLOR = Color("#AA0000")


def main():

    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    # bars

    bar = RectangleState(width=200, height=50, fill_color=BAR_COLOR)

    bar_states = [replace(bar, pos=Point2D(0, i * 80)) for i in range(-1, 2)]

    bar_elements = [
        VElement().keystates([bar_state, bar_state]) for bar_state in bar_states
    ]

    scene.add_elements(bar_elements)

    # counter

    centered_counter_start = NumberState(
        value=FROM,
        format=NumberFormat.INTEGER,
        font_family="Courier New",
        font_size=44,
        fill_color=Color("#FDBE02"),
    )
    centered_counter_end = replace(
        centered_counter_start,
        value=TO,
    )
    centered_counter_element = VElement().keystates(
        [
            centered_counter_start,
            centered_counter_end,
        ]
    )

    left_aligned_counter_start = replace(
        centered_counter_start,
        text_anchor="start",
        pos=Point2D(-90, -80),
    )
    left_aligned_counter_end = replace(
        left_aligned_counter_start,
        value=TO,
    )
    left_aligned_counter_element = VElement().keystates(
        [
            left_aligned_counter_start,
            left_aligned_counter_end,
        ]
    )

    right_aligned_counter_start = replace(
        centered_counter_start,
        text_anchor="end",
        pos=Point2D(90, 80),
    )
    right_aligned_counter_end = replace(
        right_aligned_counter_start,
        value=TO,
    )
    right_aligned_counter_element = VElement().keystates(
        [
            right_aligned_counter_start,
            right_aligned_counter_end,
        ]
    )

    scene.add_elements(
        [
            centered_counter_element,
            left_aligned_counter_element,
            right_aligned_counter_element,
        ]
    )
    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to mp4
    exporter.to_mp4(
        filename="29_counter",
        total_frames=TO - FROM + 1,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
