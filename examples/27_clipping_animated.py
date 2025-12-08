"""Basic clipping example - static clip-path"""

from dataclasses import replace
from svan2d.component.state.triangle import TriangleState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.vscene import VScene
from svan2d.velement import VElement
from svan2d.component import CircleState, RectangleState
from svan2d.core import Color
from svan2d.vscene import VSceneExporter

configure_logging(level="INFO")

# Create a scene
scene = VScene(width=400, height=400)

s1 = RectangleState(
    width=200,
    height=200,
    fill_color=Color("#FF6B6B"),
    clip_state=CircleState(radius=30),
)

s2 = replace(s1, clip_state=CircleState(radius=60))


# Rectangle clipped by a circle
clipped_rect = VElement(
    keystates=[s1, s2],
)

scene.add_element(clipped_rect)

exporter = VSceneExporter(
    scene=scene,
    converter=ConverterType.PLAYWRIGHT,
    output_dir="output/",
)

exporter.to_mp4(
    filename="27_clipping_animated.mp4",
    total_frames=30,
    framerate=30,
    png_width_px=1024,
    num_thumbnails=100,
)
