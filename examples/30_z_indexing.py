from dataclasses import replace
from svan2d.component.state.circle import CircleState
from svan2d.component.state.number import NumberFormat, NumberState
from svan2d.component.state.rectangle import RectangleState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.point2d import Point2D
from svan2d.core.logger import configure_logging
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.core.color import Color


configure_logging(level="INFO")

CENTER_CIRCLE = Color("#FDBE02")
SURROUNDING_CIRCLES = Color("#AA0000")


def main():

    # Create the scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    center_circle_start = CircleState(radius=70, fill_color=CENTER_CIRCLE)
    center_circle_end = CircleState(radius=70, fill_color=CENTER_CIRCLE, z_index=5)

    center_element = VElement().keystates([center_circle_start, center_circle_end])

    c1 = CircleState(
        radius=40, pos=Point2D(-70, 0), z_index=1, fill_color=SURROUNDING_CIRCLES
    )
    c2 = replace(c1, pos=Point2D(70, 0), z_index=2)
    c3 = replace(c1, pos=Point2D(0, -70), z_index=3)
    c4 = replace(c1, pos=Point2D(0, 70), z_index=4)

    surrounding_elements = [VElement().keystates([s, s]) for s in [c1, c2, c3, c4]]

    scene.add_element(center_element)
    scene.add_elements(surrounding_elements)

    # Export to mp4

    # Create the exporter
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="30_z_indexing",
        total_frames=60,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
