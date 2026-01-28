from dataclasses import replace
from svan2d.component import CircleState, RectangleState, TextState
from svan2d.component.state.number import NumberFormat, NumberState, Rounding
from svan2d.converter.converter_type import ConverterType
from svan2d.core import Color, Point2D
from svan2d.core.logger import configure_logging
from svan2d.transition import easing
from svan2d.velement import VElement
from svan2d.vscene import VScene, VSceneComposite, VSceneExporter

configure_logging(level="INFO")

START_COLOR = Color("#AA0000")
END_COLOR = Color("#FDBE02")


def create_timer_scene(
    background_color: Color,
    start_val: float,
    width: float = 200,
    height: float = 50,
) -> VScene:
    """Create a simple scene with a colored rectangle and label."""
    scene = VScene(width=width, height=height, background=background_color)

    start_state = NumberState(
        value=start_val,
        format=NumberFormat.INTEGER,
        font_size=40,
        font_weight="normal",
        fill_color=Color("#FFFFFF"),
        rounding=Rounding.CEIL,
    )
    end_state = replace(start_state, value=0)

    element = VElement().keystate(start_state, at=0).keystate(end_state, at=1)

    scene = scene.add_element(element)

    return scene


def create_scene(
    label: str,
    end_time: float,
    background_color: Color,
    square_width_percentage: float,
    width: float = 200,
    height: float = 150,
) -> VScene:
    """Create a simple scene with a colored rectangle and label."""
    scene = VScene(width=width, height=height, background=background_color)

    start_state = RectangleState(
        width=width * square_width_percentage,
        height=height * square_width_percentage,
        fill_color=background_color,
    )

    end_state = CircleState(
        radius=min(width, height) * 0.4,
        fill_color=END_COLOR,
    )

    scene.add_element(
        VElement()
        .keystate(start_state, at=0)
        .keystate(end_state, at=end_time)
        .keystate(end_state, at=1)
    )

    # Label text
    state = TextState(
        text=label,
        font_size=24,
        font_weight="bold",
        fill_color=Color("#FFFFFF"),
    )

    text = VElement().keystates([state, state])
    scene = scene.add_element(text)

    return scene


def main():
    # Create scenes with different sizes and colors

    row_1 = create_timer_scene(Color(0, 0, 100), 3, 350, 75)

    scene_a = create_scene(
        "A", 0.6, START_COLOR.interpolate(END_COLOR, 0), 0.4, width=200, height=150
    )
    scene_b = create_scene(
        "B", 0.7, START_COLOR.interpolate(END_COLOR, 0.25), 0.3, width=150, height=150
    )
    scene_c = create_scene(
        "C", 0.8, START_COLOR.interpolate(END_COLOR, 0.5), 0.2, width=160, height=120
    )
    scene_d = create_scene(
        "D", 0.9, START_COLOR.interpolate(END_COLOR, 0.75), 0.1, width=190, height=120
    )

    row_2 = VSceneComposite([scene_a, scene_b], direction="horizontal", gap=4)
    row_3 = VSceneComposite([scene_c, scene_d], direction="horizontal", gap=4)

    grid = VSceneComposite([row_1, row_2, row_3], direction="vertical", gap=4)

    exporter = VSceneExporter(
        grid,
        output_dir="output/",
        converter=ConverterType.PLAYWRIGHT_HTTP,
    )

    exporter.to_mp4(
        filename="37_scene_composite",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=30,
    )


if __name__ == "__main__":
    main()
