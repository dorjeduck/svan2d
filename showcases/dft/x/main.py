"""Fourier Epicycles Showcase — draw shapes using rotating circles from DFT.

Demonstrates complex multi-element composition and per-frame keystate animation.

Usage:
    python showcases/fourier/epicycles/main.py
"""

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

from elements import create_epicycle_elements
from fourier import compute_dft
from shapes import get_shape


def main():
    configure_logging(level="INFO")

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    scene_cfg = cfg["scene"]
    epi_cfg = cfg["epicycles"]
    style_cfg = cfg["style"]
    export_cfg = cfg["export"]

    total_frames = export_cfg["total_frames"]

    # 1. Sample the shape path
    samples = get_shape(
        name=epi_cfg["shape"],
        num_samples=epi_cfg["num_samples"],
        scale=epi_cfg["shape_scale"],
    )

    # 2. Compute DFT and truncate to desired number of coefficients
    coefficients = compute_dft(samples)
    coefficients = coefficients[: epi_cfg["num_coefficients"]]

    # 3. Build VElements
    elements = create_epicycle_elements(
        coefficients=coefficients,
        num_trail_vertices=epi_cfg["num_trail_vertices"],
        trail_color=Color(style_cfg["trail_color"]),
        trail_width=style_cfg["trail_width"],
        arm_color=Color(style_cfg["arm_color"]),
        arm_width=style_cfg["arm_width"],
        arm_opacity=style_cfg["arm_opacity"],
        circle_color=Color(style_cfg["circle_color"]),
        circle_width=style_cfg["circle_width"],
        circle_min_opacity=style_cfg["circle_min_opacity"],
        circle_max_opacity=style_cfg["circle_max_opacity"],
        tip_color=Color(style_cfg["tip_color"]),
        tip_radius=style_cfg["tip_radius"],
    )

    # 4. Build scene
    scene = VScene(
        width=scene_cfg["width"],
        height=scene_cfg["height"],
        background=Color(scene_cfg["background"]),
    )
    scene = scene.add_elements(elements)

    # 5. Export
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
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
