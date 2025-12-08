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
    # These states will be the starting point of the animation
    start_states = [
        TextState(
            text=f"{num:02}",
            font_family="Courier New",
            font_size=8,
            fill_color=Color("#FDBE02"),
        )
        for num in range(1, 20)
    ]

    # Arrange the numbers in a circular layout for the middle states
    middle_states = layout.circle(
        start_states,
        radius=96,
        alignment=layout.ElementAlignment.LAYOUT,
    )

    end_states = layout.spiral(
        start_states,
        radius_step=3,
        angle_step=30,
        alignment=layout.ElementAlignment.LAYOUT,
    )

    # Create a text renderer for all numbers
    renderer = TextRenderer()

    # keystate fine tuning, 4 times faster between start and middle than middle to end

    elements = [
        VElement(
            renderer=renderer,
            keystates=[(0, start_state), (0.2, middle_state), (1, end_state)],
        )
        for start_state, middle_state, end_state in zip(
            start_states, middle_states, end_states
        )
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
        filename="07_timed_keystates",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
