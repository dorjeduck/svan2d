"""Example: Word-to-word morphing

Demonstrates using FontGlyphs to morph entire words:
- "AH" -> "MIRROR" -> "AH"

Uses StateCollectionState M->N morphing to handle different letter counts.

Requires: pip install fonttools
"""

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.font import FontGlyphs
from svan2d.transition.mapping import GreedyMapper
from svan2d.transition.mapping.clustering import ClusteringMapper
from svan2d.transition.mapping.hungarian import HungarianMapper
from svan2d.transition.vertex_alignment.angular import AngularAligner
from svan2d.transition.vertex_alignment.norm import AlignmentNorm
from svan2d.velement import VElement
from svan2d.velement.morphing import MorphingConfig
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

configure_logging(level="INFO")


def main():
    # Use a system font (adjust path for your OS)
    # macOS: /Library/Fonts/Arial Unicode.ttf
    # Linux: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
    # Windows: C:/Windows/Fonts/arial.ttf
    font_path = "/Library/Fonts/Arial Unicode.ttf"

    # Load font
    font = FontGlyphs(font_path)

    # Get word states (returns StateCollectionState directly, centered at pos)
    word1 = font.get_word(
        "EMPTY",
        height=20,
        letter_spacing=1.1,
        fill_color=Color("#FDBE02"),
    )

    word2 = font.get_word(
        "MIRROR",
        height=20,
        letter_spacing=1.1,
        fill_color=Color("#E57C04"),
    )

    font.close()

    # Create scene
    scene = VScene(width=256, height=256, background=Color("#000017"))

    morphing_config = MorphingConfig(
        mapper=HungarianMapper(),
        vertex_aligner=AngularAligner(norm=AlignmentNorm.LINF),
    )

    # Single element morphs entire word
    element = (
        VElement()
        .keystate(word1, at=0.0)
        .keystate(word1, at=0.1)
        .transition(morphing_config=morphing_config)
        .keystate(word2, at=0.4)
        .keystate(word2, at=0.6)
        .transition(morphing_config=morphing_config)
        .keystate(word1, at=0.9)
        .keystate(word1, at=1.0)
    )

    scene.add_element(element)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="27_word_morphing",
        total_frames=120,
        framerate=30,
        png_width_px=1024,
    )


if __name__ == "__main__":
    main()
