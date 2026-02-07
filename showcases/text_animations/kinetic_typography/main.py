"""Kinetic Typography Showcase — per-character animation.

Builds a VSceneSequence with one scene per entrance mode (scatter, rain,
explode, spiral), connected by scene transitions. Config-driven via TOML.

Usage:
    python showcases/kinetic_typography/main.py
"""

import random
import tomllib
from pathlib import Path

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.transition.scene import Fade
from svan2d.vscene import VScene, VSceneExporter, VSceneSequence

from word_element import create_word_char_elements


def build_scene(
    words: list[str],
    palette: list[Color],
    font_path: str,
    font_size: float,
    entrance: str,
    scene_cfg: dict,
    anim_cfg: dict,
    rng: random.Random,
) -> VScene:
    """Build a single kinetic typography scene for the given entrance mode."""

    scene = VScene(
        width=scene_cfg["width"],
        height=scene_cfg["height"],
        background=Color(scene_cfg["background"]),
    )

    char_stagger = anim_cfg["char_stagger"]
    entrance_duration = anim_cfg["entrance_duration"]
    hold = anim_cfg["hold"]
    scatter_radius = anim_cfg["scatter_radius"]
    scatter_rotation = anim_cfg["scatter_rotation"]

    line_height = font_size * 1.4
    total_text_height = (len(words) - 1) * line_height
    start_y = -total_text_height / 2

    total_chars = sum(len(w.replace(" ", "")) for w in words)

    # Timing: entrance → hold → exit, normalised to [0, 1]
    entrance_phase = total_chars * char_stagger + entrance_duration
    exit_duration = entrance_duration
    exit_phase = total_chars * char_stagger + exit_duration
    raw_total = entrance_phase + hold + exit_phase
    s = 1.0 / raw_total

    char_stagger_s = char_stagger * s
    entrance_dur_s = entrance_duration * s
    exit_dur_s = exit_duration * s
    exit_phase_start = (entrance_phase + hold) * s

    elements = []
    global_char_idx = 0

    for word_idx, word in enumerate(words):
        color = palette[word_idx % len(palette)]
        y = start_y + word_idx * line_height
        word_center = Point2D(0, y)

        char_elements = create_word_char_elements(
            text=word,
            word_center=word_center,
            color=color,
            font_path=font_path,
            font_size=font_size,
            first_char_time=global_char_idx * char_stagger_s,
            char_stagger=char_stagger_s,
            entrance_duration=entrance_dur_s,
            exit_at=exit_phase_start + global_char_idx * char_stagger_s,
            exit_duration=exit_dur_s,
            entrance=entrance,
            scatter_radius=scatter_radius,
            scatter_rotation=scatter_rotation,
            rng=rng,
        )
        elements.extend(char_elements)
        global_char_idx += len(word.replace(" ", ""))

    scene = scene.add_elements(elements)
    return scene


def main():
    configure_logging(level="INFO")

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    scene_cfg = cfg["scene"]
    font_cfg = cfg["font"]
    text_cfg = cfg["text"]
    anim_cfg = cfg["animation"]
    style_cfg = cfg["style"]
    export_cfg = cfg["export"]

    words = text_cfg["lines"]
    palette = [Color(c) for c in style_cfg["palette"]]
    rng = random.Random(42)

    entrance_modes = style_cfg["entrance_modes"]

    transition = Fade(duration=0.01)

    # Build one scene per entrance mode
    scenes = []
    for mode in entrance_modes:
        sc = build_scene(
            words=words,
            palette=palette,
            font_path=font_cfg["path"],
            font_size=font_cfg["size"],
            entrance=mode,
            scene_cfg=scene_cfg,
            anim_cfg=anim_cfg,
            rng=rng,
        )
        scenes.append(sc)

    # Assemble sequence
    sequence = VSceneSequence().scene(scenes[0], duration=1)
    for i in range(1, len(scenes)):
        sequence = sequence.transition(transition)
        sequence = sequence.scene(scenes[i], duration=1)

    exporter = VSceneExporter(
        scene=sequence,
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
