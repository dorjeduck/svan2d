"""Spectrum Buildup Showcase — progressive Fourier approximation.

Each stage draws the shape with more coefficients, showing the
approximation sharpening from a rough circle to the full shape.
Cycles through all configured shapes as a sequence.

Usage:
    python showcases/fourier/spectrum_buildup/main.py
"""

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.transition.scene import Fade, Iris, Slide, Wipe, Zoom
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.vscene.vscene_sequence import VSceneSequence

from elements import create_buildup_elements
from fourier import compute_dft
from shapes import get_shape


TRANSITIONS = {
    "fade": Fade,
    "wipe": Wipe,
    "slide": Slide,
    "zoom": Zoom,
    "iris": Iris,
}


def _build_shape_scene(shape_name, cfg):
    """Build a VScene for one shape's buildup animation."""
    scene_cfg = cfg["scene"]
    buildup_cfg = cfg["buildup"]
    style_cfg = cfg["style"]

    samples = get_shape(
        name=shape_name,
        num_samples=buildup_cfg["num_samples"],
        scale=buildup_cfg["shape_scale"],
    )

    coefficients = compute_dft(samples)

    # Convert fade_rounds to normalized fade_duration
    num_stages = len(buildup_cfg["stages"])
    fade_duration = buildup_cfg["fade_rounds"] / num_stages

    elements = create_buildup_elements(
        coefficients=coefficients,
        stages=buildup_cfg["stages"],
        num_trail_vertices=buildup_cfg["num_trail_vertices"],
        color_start=Color(style_cfg["color_start"]),
        color_end=Color(style_cfg["color_end"]),
        trail_width=style_cfg["trail_width"],
        tip_color=Color(style_cfg["tip_color"]),
        tip_radius=style_cfg["tip_radius"],
        label_color=Color(style_cfg["label_color"]),
        label_font_size=style_cfg["label_font_size"],
        label_y=style_cfg["label_y"],
        fade_duration=fade_duration,
    )

    scene = VScene(
        width=scene_cfg["width"],
        height=scene_cfg["height"],
        background=Color(scene_cfg["background"]),
    )
    return scene.add_elements(elements)


def main():
    configure_logging(level="INFO")

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    buildup_cfg = cfg["buildup"]
    scene_cfg = cfg["scene"]
    export_cfg = cfg["export"]

    shapes = buildup_cfg["shapes"]
    transition_name = buildup_cfg["transition"]
    transition_frames = buildup_cfg["transition_frames"]
    frames_per_shape = export_cfg["total_frames"]

    # Total frames across all shapes + transitions
    num_transitions = len(shapes) - 1
    total_frames = frames_per_shape * len(shapes) + transition_frames * num_transitions

    # Build transition
    trans_cls = TRANSITIONS.get(transition_name, Fade)
    rel_duration = transition_frames / total_frames
    transition = trans_cls(duration=rel_duration)

    # Build sequence
    sequence = VSceneSequence(
        width=scene_cfg["width"],
        height=scene_cfg["height"],
    )

    for i, shape_name in enumerate(shapes):
        print(f"  [{i+1}/{len(shapes)}] Building {shape_name}...")
        scene = _build_shape_scene(shape_name, cfg)
        rel_shape_duration = frames_per_shape / total_frames
        sequence = sequence.scene(scene, duration=rel_shape_duration)

        if i < len(shapes) - 1:
            sequence = sequence.transition(transition)

    # Export
    exporter = VSceneExporter(
        scene=sequence,
        converter=ConverterType(export_cfg["converter"]),
        output_dir=export_cfg["output_dir"],
    )

    exporter.to_mp4(
        filename=export_cfg["filename"],
        total_frames=total_frames,
        framerate=export_cfg["framerate"],
        png_width_px=export_cfg["png_width_px"],
    )


if __name__ == "__main__":
    main()
