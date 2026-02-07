"""Text Wave Showcase — letters enter from the right riding a sine wave.

Each letter slides in from offscreen right along a continuous sine wave,
locks to its final x-position on arrival, and keeps oscillating vertically.
The wave amplitude decays smoothly so letters settle into a straight line.

Usage:
    python showcases/text_animations/text_wave/main.py
"""

import tomllib
from pathlib import Path

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.font.font_glyphs import FontGlyphs
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

from elements import create_wave_elements


def main():
    configure_logging(level="INFO")

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    scene_cfg = cfg["scene"]
    font_cfg = cfg["font"]
    wave_cfg = cfg["wave"]
    style_cfg = cfg["style"]
    export_cfg = cfg["export"]

    width = scene_cfg["width"]
    height = scene_cfg["height"]
    total_frames = export_cfg["total_frames"]

    font = FontGlyphs(font_cfg["path"])
    color = Color(style_cfg["color"])

    elements = create_wave_elements(
        font=font,
        text=wave_cfg["text"],
        font_size=font_cfg["size"],
        color=color,
        scene_width=width,
        amplitude=wave_cfg["amplitude"],
        wavelength=wave_cfg["wavelength"],
        speed=wave_cfg["speed"],
        entry_duration=wave_cfg["entry_duration"],
        stagger=wave_cfg["stagger"],
        total_frames=total_frames,
        align_rotation=wave_cfg.get("align_rotation", True),
        decay_start=wave_cfg.get("decay_start", 1.0),
        decay_end=wave_cfg.get("decay_end", 1.0),
    )

    scene = VScene(width=width, height=height, background=Color(scene_cfg["background"]))
    scene = scene.add_elements(elements)

    exporter = VSceneExporter(
        scene=scene,
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
