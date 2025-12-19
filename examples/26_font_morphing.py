"""Example: Font glyph morphing

Demonstrates using FontGlyphs to extract letter vertices and morph between:
- Letter 'A' -> Letter 'B' -> Letter 'C' -> Letter 'A'

Requires: pip install fonttools
"""

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.font import FontGlyphs
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

configure_logging(level="INFO")


def main():
    # Use a system font (adjust path for your OS)
    # macOS: /Library/Fonts/Arial Unicode.ttf
    # Linux: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
    # Windows: C:/Windows/Fonts/arial.ttf
    font_path = "/Library/Fonts/Arial Unicode.ttf"

    # Load font and extract glyphs
    font = FontGlyphs(font_path)

    # Get letter states with different colors
    letter_a = font.get_state(
        char="A",
        height=100,
        fill_color=Color("#FDBE02"),
    )

    letter_b = font.get_state(
        char="B",
        height=100,
        fill_color=Color("#E57C04"),
    )

    letter_c = font.get_state(
        char="C",
        height=100,
        fill_color=Color("#F63E02"),
    )

    font.close()

    # Create scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    # Create morphing animation: A -> B -> C -> A
    element = (
        VElement()
        .keystate(letter_a, at=0.0)
        .keystate(letter_b, at=0.33)
        .keystate(letter_c, at=0.66)
        .keystate(letter_a, at=1.0)
    )

    scene.add_element(element)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="26_font_morphing",
        total_frames=180,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
