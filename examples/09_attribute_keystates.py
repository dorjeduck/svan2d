from dataclasses import replace


from svan2d.component import TextRenderer, TextState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d import layout
from svan2d.velement import VElement
from svan2d.vscene import VScene, VSceneExporter
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
            fill_color=Color("#FDBE02"),
        )
        for num in range(1, 10)
    ]

    # Arrange the numbers along a line for start and end positions
    start_states = layout.line(states, center=Point2D(-100, 0), spacing=20, rotation=90)
    middle_states = layout.line(states, spacing=20, rotation=90)
    end_states = layout.line(states, center=Point2D(100, 0), spacing=20, rotation=90)

    # lets animate also a change of color
    middle_states = [replace(state, fill_color="#d88023") for state in end_states]
    end_states = [replace(state, fill_color=Color("#AA0000")) for state in end_states]

    # Create a text renderer for all numbers
    renderer = TextRenderer()

    elements = [
        VElement(renderer=renderer)
        .attributes(keystates_dict={"fill_color": [START_COLOR, END_COLOR]})
        .keystate(start_state, at=0)
        .keystate(middle_state, at=0.1 * (i + 1))
        .keystate(end_state, at=1)
        for i, (start_state, middle_state, end_state) in enumerate(
            zip(start_states, middle_states, end_states)
        )
    ]

    # Add all elements to the scene
    scene = scene.add_elements(elements)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to MP4 file
    exporter.to_mp4(
        filename="09_attribute_keystates",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
