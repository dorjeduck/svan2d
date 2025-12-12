from svan2d.component import TextRenderer, TextState
from svan2d.converter.converter_type import ConverterType
from svan2d import layout
from svan2d.core.point2d import Point2D
from svan2d.core.logger import configure_logging
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.core.color import Color


configure_logging(level="INFO")


def main():

    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    # Create text states for each number with consistent styling
    # These states will be the starting point of the animation
    start_states = [
        TextState(
            pos=Point2D(0, 0),  # centered (default but explicit for clarity)
            text=str(num),
            font_family="Courier New",
            font_size=20,
            fill_color=Color("#FDBE02"),
        )
        for num in range(1, 10)
    ]

    # Arrange the numbers in an elliptical layout for the end states
    end_states = layout.ellipse(
        start_states,
        rx=96,
        ry=64,
    )

    # Create a text renderer for all numbers
    renderer = TextRenderer()

    # Create visual elements from states by
    # pairing each start state with its corresponding end state
    elements = [
        VElement().renderer(renderer).keystates(states)
        for states in zip(start_states, end_states)
    ]

    # Add all elements to the scene
    scene.add_elements(elements)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to mp4
    exporter.to_mp4(
        filename="02c_simple_animation",
        total_frames=60,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
