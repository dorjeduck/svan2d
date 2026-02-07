from dataclasses import replace
from svan2d.component.state.circle import CircleState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.core.color import Color

configure_logging(level="INFO")

START_COLOR = Color("#AA0000")
END_COLOR = Color("#0AEF21")


def main():

    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    start_state = CircleState(radius=50, fill_color=START_COLOR)

    end_state = replace(start_state, fill_color=END_COLOR)

    element = (
        VElement()
        .keystate(start_state, at=0)
        .keystate([start_state, end_state], at=0.5)
        .keystate(end_state, at=1)
    )

    # Add all elements to the scene
    scene = scene.add_element(element)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.CAIROSVG,
        output_dir="output/",
    )

    # Export to MP4 file
    exporter.to_mp4(
        filename="35_dual_keystate",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
