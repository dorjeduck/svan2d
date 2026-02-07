"""Quote Poster Generator — kinetic-typography entrance, decorations, font morphing.

Config-driven showcase: swap config.toml to change the entire poster style.

Usage:
    python showcases/text_animations/quote_poster/main.py
"""

import random
import tomllib
from pathlib import Path

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.vscene import VScene, VSceneExporter

from author_elements import create_author_elements
from decorations import create_decoration_elements
from quote_elements import create_quote_elements, get_quote_block_bounds


def main():
    configure_logging(level="INFO")

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    scene_cfg = cfg["scene"]
    font_cfg = cfg["fonts"]
    text_cfg = cfg["text"]
    anim_quote = cfg["animation"]["quote"]
    anim_deco = cfg["animation"]["decorations"]
    anim_author = cfg["animation"]["author"]
    style_cfg = cfg["style"]
    export_cfg = cfg["export"]

    rng = random.Random(42)

    scene = VScene(
        width=scene_cfg["width"],
        height=scene_cfg["height"],
        background=Color(scene_cfg["background"]),
    )

    lines = text_cfg["quote_lines"]
    quote_color = Color(style_cfg["quote_color"])
    author_color = Color(style_cfg["author_color"])

    # Compute quote block bounds for positioning decorations and author
    quote_min_y, quote_max_y = get_quote_block_bounds(
        lines=lines,
        font_size=font_cfg["quote_size"],
    )

    # Author position: below the quote block + separator
    author_pos = Point2D(0, quote_max_y + 45)

    # 1. Quote characters with scatter entrance
    quote_elements = create_quote_elements(
        lines=lines,
        font_path=font_cfg["quote_path"],
        font_size=font_cfg["quote_size"],
        quote_color=quote_color,
        scatter_radius=anim_quote["scatter_radius"],
        scatter_rotation=anim_quote["scatter_rotation"],
        entrance_start=anim_quote["scatter_start"],
        entrance_end=anim_quote["scatter_end"],
        rng=rng,
    )

    # 2. Decorative circles and lines
    decoration_elements = create_decoration_elements(
        scene_width=scene_cfg["width"],
        scene_height=scene_cfg["height"],
        decoration_start=anim_deco["start"],
        decoration_end=anim_deco["end"],
        style_cfg=style_cfg,
        quote_bounds=(quote_min_y, quote_max_y),
        rng=rng,
    )

    # 3. Author name: cursive fade-in + morph to block
    author_els = create_author_elements(
        author=text_cfg["author"],
        cursive_path=font_cfg["author_cursive_path"],
        block_path=font_cfg["author_block_path"],
        block_size=font_cfg["author_block_size"],
        cursive_size=font_cfg["author_cursive_size"],
        author_color=author_color,
        author_pos=author_pos,
        fade_start=anim_author["fade_start"],
        fade_end=anim_author["fade_end"],
        morph_start=anim_author["morph_start"],
        morph_end=anim_author["morph_end"],
    )

    # Add all elements to scene
    all_elements = quote_elements + decoration_elements + author_els
    scene = scene.add_elements(all_elements)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType(export_cfg["converter"]),
        output_dir=export_cfg["output_dir"],
    )

    exporter.to_mp4(
        filename=export_cfg["filename"],
        total_frames=export_cfg["total_frames"],
        framerate=export_cfg["framerate"],
        png_width_px=export_cfg["png_width_px"],
    )


if __name__ == "__main__":
    main()
