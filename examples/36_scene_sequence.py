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


def create_scene_1() -> VScene:
    """Create first scene with animated circle."""
    scene = VScene(width=400, height=300, background=Color("#1a1a2e"))

    # Animated circle moving across screen
    start_state = CircleState(
        pos=Point2D(-150, 0),
        radius=40,
        fill_color=Color("#e94560"),
    )
    end_state = CircleState(
        pos=Point2D(150, 0),
        radius=40,
        fill_color=Color("#0f3460"),
    )
    circle = VElement().keystates([start_state, end_state])
    scene.add_element(circle)

    # Scene label
    label = VElement(
        state=TextState(
            pos=Point2D(0, 100),
            text="Scene 1",
            font_size=24,
            fill_color=Color("#ffffff"),
        )
    )
    scene.add_element(label)

    return scene


def create_scene_2() -> VScene:
    """Create second scene with animated rectangle."""
    scene = VScene(width=400, height=300, background=Color("#0f3460"))

    # Animated rectangle rotating
    start_state = RectangleState(
        pos=Point2D(0, 0),
        width=80,
        height=80,
        rotation=0,
        fill_color=Color("#e94560"),
    )
    end_state = RectangleState(
        pos=Point2D(0, 0),
        width=80,
        height=80,
        rotation=360,
        fill_color=Color("#16c79a"),
    )
    rect = VElement().keystates([start_state, end_state])
    scene.add_element(rect)

    # Scene label
    label = VElement(
        state=TextState(
            pos=Point2D(0, 100),
            text="Scene 2",
            font_size=24,
            fill_color=Color("#ffffff"),
        )
    )
    scene.add_element(label)

    return scene


def create_scene_3() -> VScene:
    """Create third scene with multiple circles."""
    scene = VScene(width=400, height=300, background=Color("#16c79a"))

    # Multiple animated circles
    colors = [Color("#e94560"), Color("#0f3460"), Color("#1a1a2e")]
    for i, color in enumerate(colors):
        start_state = CircleState(
            pos=Point2D(0, 0),
            radius=20,
            fill_color=color,
        )
        end_state = CircleState(
            pos=Point2D((i - 1) * 80, 0),
            radius=40,
            fill_color=color,
        )
        circle = VElement().keystates([start_state, end_state])
        scene.add_element(circle)

    # Scene label
    label = VElement(
        state=TextState(
            pos=Point2D(0, 100),
            text="Scene 3",
            font_size=24,
            fill_color=Color("#1a1a2e"),
        )
    )
    scene.add_element(label)

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
        filename="36_scene_sequence",
        total_frames=300,
        framerate=30,
        png_width_px=800,
    )

    print("Export complete!")


if __name__ == "__main__":
    main()
