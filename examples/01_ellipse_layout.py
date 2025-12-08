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
    states = [
        TextState(
            text=str(num),
            font_family="Courier New",
            font_size=20,
            fill_color=Color("#FDBE02"),
        )
        for num in range(1, 10)
    ]

    # Arrange the numbers in an elliptical layout
    states_layout = layout.ellipse(
        states,
        rx=96,
        ry=64,
    )

    # Create a text renderer for all numbers
    renderer = TextRenderer()

    # Create visual elements from states
    # VElements in Svan2D are the combination of one renderer and one or more states
    elements = [
        VElement(
            renderer=renderer,
            state=state,
        )
        for state in states_layout
    ]

    # Add all elements to the scene
    scene.add_elements(elements)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    # Export to PNG file
    exporter.export(
        filename="01_ellipse_layout", formats=["svg", "png"], png_width_px=1024
    )


if __name__ == "__main__":
    main()
