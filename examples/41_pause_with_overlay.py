

from svan2d.core import (
    Color,
    Point2D,
    configure_logging,
)
from svan2d.converter import ConverterType
from svan2d.velement import VElement
from svan2d.vscene import (
    VScene,
    VSceneExporter,
)
from svan2d.primitive.state import (
    CircleState,
    TextState,
)
from svan2d.primitive.renderer import (
    CircleRenderer,
    TextRenderer,
)
configure_logging(level="INFO")

START_COLOR = Color("#FDBE02")
END_COLOR = Color("#AA0000")

def main():

    scene = VScene(width=512, height=256, background=Color("#000017"))

    # A circle moves from left to right across the canvas.
    moving_circle = (
        VElement(renderer=CircleRenderer())
        .keystate(
            CircleState(pos=Point2D(-220, 0), radius=20, fill_color=START_COLOR),
            at=0.0,
        )
        .keystate(
            CircleState(pos=Point2D(220, 0), radius=20, fill_color=END_COLOR),
            at=1.0,
        )
    )
    scene = scene.add_element(moving_circle)

    # Overlay shown only during the pause window.
    overlay = VElement(
        renderer=TextRenderer(),
        state=TextState(
            text="PAUSED",
            font_family="Courier New",
            font_size=48,
            fill_color=Color("#FFFFFF"),
        ),
    )

    # Pause at the timeline midpoint, occupying 40% of the rendered output.
    # fade=0.25 → first/last quarter of the pause window are fade-in / fade-out.
    scene = scene.add_pause(at=0.5, fraction=0.4, overlay=overlay, fade=0.25)

    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="41_pause_with_overlay",
        total_frames=90,
        framerate=30,
        png_width_px=1024,
    )

if __name__ == "__main__":
    main()
