from svan2d.transition import easing
from svan2d import layout
from svan2d.core import (
    Color,
    Point2D,
    configure_logging,
)
from svan2d.converter import ConverterType
from svan2d.velement import VElement
from svan2d.vscene import (
    VScene,
    VSceneExporter,
)
from svan2d.primitive.state import TextState
from svan2d.primitive.renderer import TextRenderer
from dataclasses import replace

configure_logging(level="INFO")

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
    middle_states = [
        replace(state, fill_color=Color("#FDBE02")) for state in end_states
    ]
    end_states = [replace(state, fill_color=Color("#AA0000")) for state in end_states]

    # Create a text renderer for all numbers
    renderer = TextRenderer()

    # overriding the default easing for the x field for each element
    elements = [
        VElement(renderer=renderer)
        .attributes(easing_dict={"pos": easing.linear})
        .keystates(states, at=[0, 0.1 * (i + 1), 1])
        for i, states in enumerate(zip(start_states, middle_states, end_states))
    ]

    # Add all elements to the scene
    scene = scene.add_elements(elements)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    # Export to MP4 file
    exporter.to_mp4(
        filename="08_keystates_variety",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )

if __name__ == "__main__":
    main()
