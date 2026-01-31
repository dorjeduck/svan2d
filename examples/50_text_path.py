"""Text as paths for smooth animation.

Demonstrates TextPathState which renders text as SVG paths instead of
<text> elements. This eliminates font hinting artifacts during scaling,
rotation, and other transformations.

Requires: pip install svan2d[font]
"""

from dataclasses import replace

from svan2d.component.state import TextPathState
from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

configure_logging(level="INFO")

# Font path - adjust for your system
# macOS: /System/Library/Fonts/Supplemental/Arial.ttf
# Linux: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
# Windows: C:/Windows/Fonts/arial.ttf
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"


def main():
    scene = VScene(width=400, height=400, background=Color("#1a1a2e"))

    # Create text states at different scales and rotations
    # TextPathState ensures smooth animation without jitter

    text_start = TextPathState(
        text="42",
        font_path=FONT_PATH,
        font_size=60,
        fill_color=Color("#e94560"),
        pos=Point2D(0, 0),
        scale=0.3,
        rotation=0,
    )

    text_mid = replace(
        text_start,
        scale=1.5,
        rotation=180,
        fill_color=Color("#ffffff"),
    )

    text_end = replace(
        text_start,
        scale=1.0,
        rotation=360,
        fill_color=Color("#0000ff"),
    )

    # Create animated element with easing
    element = (
        VElement()
        .keystate(text_start, at=0.0)
        .transition(
            easing_dict={"scale": easing.out_elastic, "rotation": easing.in_out}
        )
        .keystate(text_mid, at=0.5)
        .transition(easing_dict={"scale": easing.in_out_back})
        .keystate(text_end, at=1.0)
    )

    scene = scene.add_element(element)

    # Add a second example: multiple characters scaling independently
    chars = "PATH"
    colors = ["#ff6b6b", "#4ecdc4", "#ffe66d", "#95e1d3"]

    for i, (char, color) in enumerate(zip(chars, colors)):
        offset_x = (i - 1.5) * 70

        char_start = TextPathState(
            text=char,
            font_path=FONT_PATH,
            font_size=40,
            fill_color=Color(color),
            pos=Point2D(offset_x, 120),
            scale=0.0,
        )

        char_end = replace(char_start, scale=1.0)

        # Staggered appearance
        appear_time = i * 0.15

        char_element = (
            VElement()
            .keystate(char_start, at=appear_time)
            .transition(easing_dict={"scale": easing.out_back})
            .keystate(char_end, at=min(appear_time + 0.3, 1.0))
        )

        scene = scene.add_element(char_element)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="50_text_path",
        total_frames=90,
        framerate=30,
        png_width_px=800,
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
