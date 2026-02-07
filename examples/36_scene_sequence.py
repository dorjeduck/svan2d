"""Example: Scene Transitions

Demonstrates VSceneSequence with various scene transition effects:
- Fade: Crossfade between scenes
- Wipe: Directional reveal
- Slide: Scenes slide in/out
- Zoom: Zoom effect
- Iris: Circular reveal
"""

from svan2d.component import CircleState, RectangleState, TextState
from svan2d.converter.converter_type import ConverterType
from svan2d.core import Color, Point2D
from svan2d.core.logger import configure_logging
from svan2d.transition import easing
from svan2d.transition.scene import Fade, Wipe
from svan2d.velement import VElement
from svan2d.vscene import VScene, VSceneExporter, VSceneSequence


configure_logging(level="INFO")

# Base colors
COLOR_1 = Color("#FDBE02")
COLOR_2 = Color("#AA0000")


def create_scene_1() -> VScene:
    """Create first scene with animated circle."""
    scene = VScene(width=400, height=400, background=COLOR_2.interpolate(COLOR_1, 0.1))

    # Animated circle moving across screen
    start_state = CircleState(
        pos=Point2D(-130, 0),
        radius=50,
        fill_color=COLOR_1,
    )
    end_state = CircleState(
        pos=Point2D(130, 0),
        radius=50,
        fill_color=COLOR_2,
    )
    circle = VElement().keystates([start_state, end_state])
    scene = scene.add_element(circle)

    # Scene label
    label_state = TextState(
        pos=Point2D(0, 130),
        text="Scene 1",
        font_size=28,
        fill_color=COLOR_1.interpolate(COLOR_2, 0.25),
    )
    label = VElement().keystates([label_state, label_state])
    scene = scene.add_element(label)

    return scene


def create_scene_2() -> VScene:
    """Create second scene with animated rectangle."""
    scene = VScene(width=400, height=400, background=COLOR_1.interpolate(COLOR_2, 0.5))

    # Animated rectangle rotating
    start_state = RectangleState(
        pos=Point2D(0, 0),
        width=100,
        height=100,
        rotation=0,
        fill_color=COLOR_1,
    )
    end_state = RectangleState(
        pos=Point2D(0, 0),
        width=100,
        height=100,
        rotation=360,
        fill_color=COLOR_2,
    )
    rect = VElement().keystates([start_state, end_state])
    scene = scene.add_element(rect)

    # Scene label
    label_state = TextState(
        pos=Point2D(0, 130),
        text="Scene 2",
        font_size=28,
        fill_color=COLOR_1.interpolate(COLOR_2, 0.75),
    )
    label = VElement().keystates([label_state, label_state])
    scene = scene.add_element(label)

    return scene


def create_scene_3() -> VScene:
    """Create third scene with multiple circles."""
    scene = VScene(width=400, height=400, background=COLOR_2.interpolate(COLOR_1, 0.75))

    # Multiple animated circles with interpolated colors
    colors = [
        COLOR_1,
        COLOR_1.interpolate(COLOR_2, 0.5),
        COLOR_2,
    ]
    for i, color in enumerate(colors):
        start_state = CircleState(
            pos=Point2D(0, 0),
            radius=25,
            fill_color=color,
        )
        end_state = CircleState(
            pos=Point2D((i - 1) * 100, 0),
            radius=50,
            fill_color=color,
        )
        circle = VElement().keystates([start_state, end_state])
        scene = scene.add_element(circle)

    # Scene label
    label_state = TextState(
        pos=Point2D(0, 130),
        text="Scene 3",
        font_size=28,
        fill_color=COLOR_2,
    )
    label = VElement().keystates([label_state, label_state])
    scene = scene.add_element(label)

    return scene


def main():
    # Create scenes
    scene1 = create_scene_1()
    scene2 = create_scene_2()
    scene3 = create_scene_3()

    # Build sequence with different transitions
    sequence = (
        VSceneSequence()
        .scene(scene1, duration=1)
        .transition(Fade(duration=0.25, easing=easing.in_out, overlapping=True))
        .scene(scene2, duration=1)
        .transition(Wipe(direction="left", duration=0.25, overlapping=True))
        .scene(scene3, duration=1)
    )

    print(f"Created sequence: {sequence}")

    # Create the exporter (works with VSceneSequence just like VScene)
    exporter = VSceneExporter(
        scene=sequence,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    # Export to MP4
    exporter.to_mp4(
        filename="037_scene_sequences",
        total_frames=300,
        framerate=30,
        png_width_px=1024,
        num_thumbnails=100,
    )

    print("Export complete!")


if __name__ == "__main__":
    main()
