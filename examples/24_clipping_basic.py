"""Basic clipping example - static clip-path"""

from svan2d.component.state.triangle import TriangleState
from svan2d.converter.converter_type import ConverterType
from svan2d.vscene import VScene
from svan2d.velement import VElement
from svan2d.component import CircleState, RectangleState
from svan2d.core import Color
from svan2d.vscene import VSceneExporter

# Create a scene
scene = VScene(width=400, height=400)

# Rectangle clipped by a circle
clipped_rect = VElement(
    state=RectangleState(
        width=200,
        height=200,
        fill_color=Color("#FF6B6B"),
        clip_state=TriangleState(size=30, x=-50, rotation=90),
    )
)

scene.add_element(clipped_rect)

exporter = VSceneExporter(
    scene=scene,
    converter=ConverterType.PLAYWRIGHT,
    output_dir="output/",
)
exporter.export("24_clipping_basic", formats=["svg"])
