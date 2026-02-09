"""Shape Morphing Showcase — smooth shape transitions via Fourier interpolation.

Morphs between shapes by blending their Fourier coefficients in the
frequency domain, producing smooth organic transitions.

Usage:
    python showcases/fourier/shape_morphing/main.py
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

from elements import create_morphing_elements
from fourier import compute_dft
from shapes import get_shape


def main():
    configure_logging(level="INFO")

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    scene_cfg = cfg["scene"]
    morph_cfg = cfg["morphing"]
    style_cfg = cfg["style"]
    export_cfg = cfg["export"]

    total_frames = export_cfg["total_frames"]
    num_coefficients = morph_cfg["num_coefficients"]

    # Compute DFT for each shape
    shape_coefficients = []
    for shape_name in morph_cfg["shapes"]:
        samples = get_shape(
            name=shape_name,
            num_samples=morph_cfg["num_samples"],
            scale=morph_cfg["shape_scale"],
        )
        coeffs = compute_dft(samples)[:num_coefficients]
        shape_coefficients.append(coeffs)

    elements = create_morphing_elements(
        shape_coefficients=shape_coefficients,
        trail_color=Color(style_cfg["trail_color"]),
        trail_width=style_cfg["trail_width"],
    )

    scene = VScene(
        width=scene_cfg["width"],
        height=scene_cfg["height"],
        background=Color(scene_cfg["background"]),
    )
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
