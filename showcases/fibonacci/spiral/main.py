"""Fibonacci Spiral / Golden Ratio showcase.

Squares appear in Fibonacci sequence building a golden rectangle,
with a spiral curve drawn progressively on top.
"""

import tomllib
from pathlib import Path

import data_prep
from square_elements import create_square_elements
from spiral_element import create_spiral_element
from camera import build_camera_scale, apply_camera
from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.transition import easing
from svan2d.vscene.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

configure_logging(level="INFO")


def main():
    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    data = data_prep.prepare(cfg)
    w, h = cfg["scene"]["width"], cfg["scene"]["height"]

    scale_fn = build_camera_scale(data, w, h)

    scene = VScene(
        width=w,
        height=h,
        background=Color(cfg["scene"]["background"]),
        timeline_easing=easing.in_quad,
    )
    scene = scene.add_elements(create_square_elements(data, cfg["style"], scale_fn))
    scene = scene.add_element(
        create_spiral_element(data.spiral, cfg["style"], scale_fn)
    )
    scene = apply_camera(scene, data, scale_fn)

    # Export
    output_dir = cfg["export"]["output_dir"]
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    exporter = VSceneExporter(
        scene,
        output_dir=output_dir,
        converter=ConverterType(cfg["export"]["converter"]),
    )
    exporter.to_mp4(
        cfg["export"]["filename"],
        total_frames=cfg["animation"]["total_frames"],
        framerate=cfg["animation"]["framerate"],
        png_width_px=cfg["export"]["png_width_px"],
    )


if __name__ == "__main__":
    main()
