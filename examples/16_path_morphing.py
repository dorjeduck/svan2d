from svan2d.core import (
    Color,
    configure_logging,
)
from svan2d.converter import ConverterType
from svan2d.velement import VElement
from svan2d.vscene import (
    VScene,
    VSceneExporter,
)
from svan2d.primitive.state import PathState
from svan2d.primitive.renderer import PathRenderer
from dataclasses import replace

configure_logging(level="INFO")

START_COLOR = Color("#FDBE02")
END_COLOR = Color("#AA0000")

START_PATH = "M -100,0 L 100,0"
END_PATH = "M -100,0 C -50,-100 50,100 100,0"

def main():

    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    start_state = PathState(
        data=START_PATH,
        fill_color=None,
        stroke_color=START_COLOR,
        stroke_width=4,
    )

    end_state = replace(
        start_state,
        data=END_PATH,
        stroke_color=END_COLOR,
        stroke_width=8,
        stroke_opacity=0.5,
    )

    # Create a text renderer for all numbers
    renderer = PathRenderer()

    element = VElement(renderer=renderer).keystates([start_state, end_state])

    # Add all elements to the scene
    scene = scene.add_element(element)

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    # Export to mp4
    exporter.to_mp4(
        filename="18_path_morphing",
        total_frames=60,
        framerate=30,
        png_width_px=1024,
    )

if __name__ == "__main__":
    main()
