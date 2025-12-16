from svan2d.component import TextRenderer, TextState
from svan2d.converter.converter_type import ConverterType
from svan2d import layout
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.core.logger import configure_logging
from svan2d.velement import VElement
from svan2d.velement.keystate import KeyState
from svan2d.velement.transition import TransitionConfig
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

    x_shifts = [-100, -50, 50, 100]

    all_states = [
        layout.line(states, center=Point2D(x_shift, 0), spacing=20, rotation=90)
        for x_shift in x_shifts
    ]

    # Create a text renderer for all numbers
    renderer = TextRenderer()

    # overriding the default easing for the x field for each element
    elements = [
        VElement(renderer=renderer)
        .attributes(
            easing_dict={"pos": easing.linear},
            keystates_dict={"fill_color": [START_COLOR, END_COLOR]},
        )
        .keystate(state_a, at=0)
        .keystate(state_b, at=0.25)
        .transition(
            easing_dict={"pos": easing.in_out_sine if i % 2 == 1 else easing.linear}
        )
        .keystate(state_c, at=0.75)
        .keystate(state_d, at=1)
        for i, (
            state_a,
            state_b,
            state_c,
            state_d,
        ) in enumerate(zip(*all_states))
    ]

    # Add all elements to the scene
    scene.add_elements(elements)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to MP4 file
    exporter.to_mp4(
        filename="11_segment_easing",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
