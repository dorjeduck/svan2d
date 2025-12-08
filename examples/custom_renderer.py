from dataclasses import replace
import drawsvg as dw
from typing import Optional
from svgpy.component.renderer.circle import CircleRenderer
from svgpy.component.state.circle import CircleState
from svgpy.converter.converter_type import ConverterType
from svgpy.core.logger import configure_logging
from svgpy.velement import VElement
from svgpy.vscene import VScene
from svgpy.vscene.vscene_exporter import VSceneExporter
from svgpy.core.color import Color

configure_logging(level="INFO")


class CustomCircleRenderer(CircleRenderer):

    # renderer in Svan2D return drawsvg DrawingElements
    def render(
        self, state: "CircleState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Group:

        s1 = replace(state, x=state.x - state.radius)

        s2 = replace(
            state,
            x=state.x + state.radius,
            opacity=state.opacity / 2,
        )

        g = dw.Group()

        for s in [s1, s2]:
            g.append(super().render(s, drawing))

        return g


BASE_COLOR = Color("#FDBE02")

# create the scene
scene = VScene(width=256, height=256, background=Color("#000017"))

# create one circle state
circle_state = CircleState(radius=30, fill_color=BASE_COLOR)

# glue state to the custom circle renderer
custom_circle_element = VElement(renderer=CustomCircleRenderer(), state=circle_state)

# Add element to the scene
scene.add_element(custom_circle_element)

# Create the exporter
exporter = VSceneExporter(
    scene=scene,
    converter=ConverterType.PLAYWRIGHT,
    output_dir="output/",
)

# Export to PNG file
exporter.export(filename="custom_renderer", formats=["svg", "png"], png_width_px=1024)
