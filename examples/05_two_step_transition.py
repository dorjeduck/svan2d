from svan2d.component import TextRenderer, TextState
from svan2d.converter.converter_type import ConverterType
from svan2d import layout
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
    start_states = [
        TextState(
            text=str(num),
            font_family="Courier New",
            font_size=20,
            fill_color=Color("#FDBE02"),
        )
        for num in range(1, 10)
    ]

    # grid and circle layout for the transition
    middle_states = layout.grid(start_states, cols=3, spacing_h=20, spacing_v=20)
    end_states = layout.circle(
        start_states, radius=80, alignment=layout.ElementAlignment.LAYOUT
    )

    # Create a text renderer for all numbers
    renderer = TextRenderer()

    # Create visual elements from states
    # VElements in Svan2D are the combination of one renderer and one or more states
    elements = [
        VElement(
            renderer=renderer,
            keystates=states,
        )
        for states in zip(start_states, middle_states, end_states)
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
        filename="05_two_step_transition.mp4",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
