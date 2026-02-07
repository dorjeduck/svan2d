from svan2d.component import CircleState, RectangleState, TextState
from svan2d.core import Color, Point2D
from svan2d.core.logger import configure_logging
from svan2d.transition import easing
from svan2d.transition.scene import Fade, Iris, Slide, Wipe, Zoom
from svan2d.velement import VElement
from svan2d.vscene import VScene, VSceneSequence


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
    scene = scene.add_element(circle)

    # Scene label
    label = VElement(
        state=TextState(
            pos=Point2D(0, 100),
            text="Scene 1",
            font_size=24,
            fill_color=Color("#ffffff"),
        )
    )
    scene = scene.add_element(label)

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
    scene = scene.add_element(rect)

    # Scene label
    label = VElement(
        state=TextState(
            pos=Point2D(0, 100),
            text="Scene 2",
            font_size=24,
            fill_color=Color("#ffffff"),
        )
    )
    scene = scene.add_element(label)

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
        scene = scene.add_element(circle)

    # Scene label
    label = VElement(
        state=TextState(
            pos=Point2D(0, 100),
            text="Scene 3",
            font_size=24,
            fill_color=Color("#1a1a2e"),
        )
    )
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
        .scene(scene1, duration=0.3)
        .transition(Fade(duration=0.1, easing=easing.in_out))
        .scene(scene2, duration=0.25)
        .transition(Wipe(direction="left", duration=0.1))
        .scene(scene3, duration=0.25)
    )

    print(f"Created sequence: {sequence}")

    # Export to MP4
    sequence.to_mp4(
        filename="output/35_scene_transitions.mp4",
        total_frames=90,
        framerate=30,
        png_width_px=800,
    )


    print("Export complete!")


def demo_all_transitions():
    """Demo showcasing each transition type individually."""
    scene1 = create_scene_1()
    scene2 = create_scene_2()

    # Dictionary of all transition types to demo
    transitions = {
        "fade": Fade(duration=0.3, easing=easing.in_out),
        "wipe_left": Wipe(direction="left", duration=0.3),
        "wipe_right": Wipe(direction="right", duration=0.3),
        "wipe_up": Wipe(direction="up", duration=0.3),
        "wipe_down": Wipe(direction="down", duration=0.3),
        "slide_left": Slide(direction="left", duration=0.3),
        "slide_right": Slide(direction="right", duration=0.3),
        "zoom_in": Zoom(direction="in", duration=0.3),
        "zoom_out": Zoom(direction="out", duration=0.3),
        "iris_open": Iris(direction="open", duration=0.3),
        "iris_close": Iris(direction="close", duration=0.3),
    }

    for name, transition in transitions.items():
        print(f"Exporting {name} transition...")
        sequence = (
            VSceneSequence()
            .scene(scene1, duration=0.35)
            .transition(transition)
            .scene(scene2, duration=0.35)
        )


    print("All transitions exported!")


if __name__ == "__main__":
    main()
    # Uncomment to export individual transition demos:
    # demo_all_transitions()
