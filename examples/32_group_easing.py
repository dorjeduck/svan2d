from svan2d.component.state.circle import CircleState
from svan2d.component.state.square import SquareState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement import VElement
from svan2d.velement.velement_group import VElementGroup, VElementGroupState
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter


configure_logging(level="INFO")


OUTER_COLOR = Color("#FDBE02")
CENTER_COLOR = Color("#AA0000")


def main():

    # Simple zoom-out with animate_camera()
    scene = VScene(
        width=600,
        height=600,
        background=Color("#000017"),
    )

    # Create circles in a grid pattern
    elements = []
    for i in range(-2, 3):
        for j in range(-2, 3):

            dist = (i**2 + j**2) ** 0.5
            t = dist / (2 * 2**0.5)
            s1 = SquareState(
                size=4,
                pos=Point2D(i * 20, j * 20),
                fill_color=CENTER_COLOR.interpolate(OUTER_COLOR, t),
            )
            s2 = CircleState(
                radius=30,
                pos=Point2D(i * 80, j * 80),
                fill_color=CENTER_COLOR.interpolate(OUTER_COLOR, t),
            )

            elements.append(VElement().keystates([s1, s2]))

    vg1 = VElementGroup(
        elements=elements[:12],
        group_easing=easing.out_cubic,
    )
    vg2 = VElementGroup(
        elements=elements[13:],
        group_easing=easing.in_cubic,
    )

    scene.add_elements([vg1, elements[12], vg2])

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.CAIROSVG,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="32_group_easing",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
