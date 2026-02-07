"""Countdown Showcase — digits morph 3 -> 2 -> 1 -> GO with color transitions.

Config-driven: change config.toml to adjust font, colors, timing, and sequence.

Usage:
    python showcases/text_animations/countdown/main.py
"""

import tomllib
from pathlib import Path

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.font import FontGlyphs
from svan2d.transition.mapping.explicit import ExplicitMapper
from svan2d.transition.vertex_alignment.angular import AngularAligner
from svan2d.velement import VElement
from svan2d.velement.morphing import MorphingConfig
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter


def load_config():
    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def build_states(cfg):
    """Build StateCollectionState for each item in the countdown sequence."""
    font_cfg = cfg["fonts"]
    countdown_cfg = cfg["countdown"]
    style_cfg = cfg["style"]
    start = countdown_cfg["start"]
    finale = countdown_cfg.get("finale", "GO")
    sequence = [str(n) for n in range(start, 0, -1)] + [finale]
    colors = [Color(c) for c in style_cfg["colors"]]

    font = FontGlyphs(font_cfg["path"])

    states = []
    for i, item in enumerate(sequence):
        color = colors[i % len(colors)]
        if len(item) == 1:
            state = font.get_state(item, height=font_cfg["digit_size"], fill_color=color)
        else:
            state = font.get_word(item, height=font_cfg["go_size"], fill_color=color)
        states.append(state)

    font.close()
    return states


def compute_timeline(n_items, hold_ratio, morph_ratio):
    """Compute normalised [0, 1] time points for holds and morphs.

    Layout: hold0 | morph0 | hold1 | morph1 | ... | holdN
    Returns list of (hold_start, hold_end) for each item.
    """
    total_parts = n_items * hold_ratio + (n_items - 1) * morph_ratio
    hold_norm = hold_ratio / total_parts
    morph_norm = morph_ratio / total_parts

    times = []
    cursor = 0.0
    for i in range(n_items):
        hold_start = cursor
        hold_end = cursor + hold_norm
        times.append((hold_start, hold_end))
        cursor = hold_end
        if i < n_items - 1:
            cursor += morph_norm

    # Snap last hold_end to 1.0 to avoid float drift
    times[-1] = (times[-1][0], 1.0)
    return times


def build_element(states, timeline):
    """Build VElement chain with hold-morph-hold pattern."""
    morphing_config = MorphingConfig(
        mapper=ExplicitMapper(),
        vertex_aligner=AngularAligner(),
    )

    element = VElement()

    for i, (state, (hold_start, hold_end)) in enumerate(zip(states, timeline)):
        if i == 0:
            element = element.keystate(state, at=hold_start)
        element = element.keystate(state, at=hold_end)

        # Add morph transition to next state
        if i < len(states) - 1:
            element = element.transition(morphing_config=morphing_config)
            next_hold_start = timeline[i + 1][0]
            element = element.keystate(states[i + 1], at=next_hold_start)

    return element


def main():
    configure_logging(level="INFO")

    cfg = load_config()
    scene_cfg = cfg["scene"]
    countdown_cfg = cfg["countdown"]
    export_cfg = cfg["export"]

    states = build_states(cfg)

    timeline = compute_timeline(
        n_items=len(states),
        hold_ratio=countdown_cfg["hold_ratio"],
        morph_ratio=countdown_cfg["morph_ratio"],
    )

    element = build_element(states, timeline)

    scene = VScene(
        width=scene_cfg["width"],
        height=scene_cfg["height"],
        background=Color(scene_cfg["background"]),
    ).add_element(element)

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
