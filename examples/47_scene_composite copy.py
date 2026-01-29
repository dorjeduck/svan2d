"""Example: VSceneComposite - spatial composition of scenes.

Demonstrates:
- Horizontal stacking of scenes
- Vertical stacking of scenes
- Nesting composites to create grids
- Animated composite export
"""

from svan2d.component import CircleState, RectangleState, TextState
from svan2d.converter.converter_type import ConverterType
from svan2d.core import Color, Point2D
from svan2d.core.logger import configure_logging
from svan2d.transition import easing
from svan2d.velement import VElement
from svan2d.vscene import VScene, VSceneComposite, VSceneExporter

configure_logging(level="INFO")


def create_scene(
    label: str, color: Color, width: float = 200, height: float = 150
) -> VScene:
    """Create a simple scene with a colored rectangle and label."""
    scene = VScene(width=width, height=height, background=Color("#FFFFFF"))

    # Background rectangle
    rect = VElement(
        state=RectangleState(
            width=width * 0.8,
            height=height * 0.8,
            fill_color=color,
            stroke_color=Color("#000000"),
            stroke_width=2,
        )
    )
    scene = scene.add_element(rect)

    # Label text
    text = VElement(
        state=TextState(
            text=label,
            font_size=24,
            font_weight="bold",
            fill_color=Color("#000000"),
        )
    )
    scene = scene.add_element(text)

    return scene


def create_animated_scene(
    color: Color, width: float = 200, height: float = 150
) -> VScene:
    """Create a scene with an animated circle."""
    scene = VScene(width=width, height=height, background=Color(12, 12, 12))

    # Animated circle
    start = CircleState(
        pos=Point2D(-width / 4, 0),
        radius=20,
        fill_color=color,
    )
    end = CircleState(
        pos=Point2D(width / 4, 0),
        radius=30,
        fill_color=Color(12, 12, 12),
    )
    circle = VElement().keystates([start, end])
    scene = scene.add_element(circle)

    return scene


def main():
    # Create scenes with different sizes and colors
    scene_a = create_scene("A", Color("#FF6B6B"), width=200, height=150)
    scene_b = create_scene("B", Color("#4ECDC4"), width=150, height=150)
    scene_c = create_scene("C", Color("#FFE66D"), width=180, height=120)
    scene_d = create_scene("D", Color("#95E1D3"), width=160, height=180)

    # Example 1: Horizontal stack
    row = VSceneComposite([scene_a, scene_b, scene_c], direction="horizontal", gap=10)
    print(f"Horizontal composite: {row}")

    # Export horizontal stack to SVG
    row.to_svg(filename="output/37a_horizontal_composite.svg")

    # Example 2: Vertical stack
    column = VSceneComposite([scene_a, scene_b], direction="vertical", gap=10)
    print(f"Vertical composite: {column}")

    column.to_svg(filename="output/37b_vertical_composite.svg")

    # Example 3: Nested composites (2x2 grid)
    row1 = VSceneComposite([scene_a, scene_b], direction="horizontal", gap=5)
    row2 = VSceneComposite([scene_c, scene_d], direction="horizontal", gap=5)
    grid = VSceneComposite([row1, row2], direction="vertical")
    print(f"Grid composite: {grid}")

    grid.to_svg(filename="output/37c_grid_composite.svg")

    # Example 4: Animated composite
    anim_scene1 = create_animated_scene(Color("#FF6B6B"))
    anim_scene2 = create_animated_scene(Color("#4ECDC4"))
    anim_scene3 = create_animated_scene(Color("#FFE66D"))

    animated_row = VSceneComposite(
        [anim_scene1, anim_scene2, anim_scene3],
        direction="horizontal",
        gap=10,
    )

    VSceneExporter(
        animated_row, output_dir="output/", converter=ConverterType.PLAYWRIGHT_HTTP
    ).to_mp4(
        filename="37d_animated_composite",
        total_frames=60,
        framerate=30,
    )


if __name__ == "__main__":
    main()
