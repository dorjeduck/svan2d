"""Author name: fade-in + font morphing (block → cursive) using FontGlyphs."""

from dataclasses import replace

from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.font import FontGlyphs
from svan2d.transition import easing
from svan2d.transition.mapping.explicit import ExplicitMapper
from svan2d.transition.vertex_alignment.angular import AngularAligner
from svan2d.velement import VElement
from svan2d.velement.morphing import MorphingConfig


def create_author_elements(
    author: str,
    cursive_path: str,
    block_path: str,
    block_size: float,
    cursive_size: float,
    author_color: Color,
    author_pos: Point2D,
    fade_start: float,
    fade_end: float,
    morph_start: float,
    morph_end: float,
) -> list[VElement]:
    """Create a single VElement for the author: fade-in block → hold → morph to cursive.

    Uses FontGlyphs for both fonts so the morph is seamless.
    """
    block_font = FontGlyphs(block_path)
    cursive_font = FontGlyphs(cursive_path)

    block_word = block_font.get_word(
        author,
        height=block_size,
        fill_color=author_color,
        pos=author_pos,
    )
    cursive_word = cursive_font.get_word(
        author,
        height=cursive_size,
        fill_color=author_color,
        pos=author_pos,
    )

    block_font.close()
    cursive_font.close()

    block_hidden = replace(block_word, opacity=0.0)

    morphing_config = MorphingConfig(
        mapper=ExplicitMapper(),
        vertex_aligner=AngularAligner(),
    )

    # Single element: fade-in block → hold → morph to cursive → hold
    element = (
        VElement()
        .keystate(block_hidden, at=fade_start)
        .transition(easing_dict={"opacity": easing.out_cubic})
        .keystate(block_word, at=fade_end)
        .keystate(block_word, at=morph_start)
        .transition(morphing_config=morphing_config)
        .keystate(cursive_word, at=morph_end)
        .keystate(cursive_word, at=1.0)
    )

    return [element]
