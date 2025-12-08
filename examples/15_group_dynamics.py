from dataclasses import replace

from svan2d.component import TextRenderer, TextState
from svan2d.converter.converter_type import ConverterType
from svan2d import layout
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.core.logger import configure_logging
from svan2d.velement import VElement
from svan2d.velement.velement_group import VElementGroup, VElementGroupState
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.core.color import Color

configure_logging(level="INFO")

START_COLOR = Color("#FDBE02")
END_COLOR = Color("#AA0000")


def main():

    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    # Create text states for each number with consistent styling
    states = [
        TextState(
            text=str(num),
            font_family="Courier New",
            font_size=20,
        )
        for num in range(1, 10)
    ]

    x_shifts = [-100, 60]

    all_states = [
        layout.line(states, center=Point2D(x_shift, 0), spacing=20, rotation=90)
        for x_shift in x_shifts
    ]

    # Create a text renderer for all numbers
    renderer = TextRenderer()

    # overriding the default easing for the x field for each element
    elements = [
        VElement(
            renderer=renderer,
            keystates=states,
            attribute_easing={"pos": easing.linear},
            attribute_keystates={"fill_color": [START_COLOR, END_COLOR]},
        )
        for states in zip(*all_states)
    ]

    g_start_state = VElementGroupState()

    g1_end_state = VElementGroupState(rotation=75, transform_origin_x=x_shifts[1] / 2)
    g2_end_state = VElementGroupState(rotation=-75, transform_origin_x=x_shifts[1] / 2)

    g1 = VElementGroup(
        elements=elements[:4],
        keystates=[
            (0, g_start_state),
            (0.5, g_start_state),
            (1, g1_end_state),
        ],
    )
    g2 = VElementGroup(
        elements=elements[5:],
        keystates=[
            (0, g_start_state),
            (0.5, g_start_state),
            (1, g2_end_state),
        ],
    )
    scene.add_elements([g1, g2])

    # adding the middle element as it is not part of any group
    scene.add_element(elements[4])

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to MP4 file
    exporter.to_mp4(
        filename="15_group_dynamics",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
