"""Phyllotaxis (sunflower seed pattern) showcase.

Seeds appear one by one following Vogel's model, then spiral
families light up with color revealing the Fibonacci structure.
"""

import tomllib
from pathlib import Path

import data_prep
from seed_elements import create_seed_elements, compute_max_extent
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

    phyl_data = data_prep.prepare(cfg)
    w, h = cfg["scene"]["width"], cfg["scene"]["height"]
    cam_cfg = cfg["camera"]

    scene = VScene(
        width=w,
        height=h,
        background=Color(cfg["scene"]["background"]),
    )

    elements = create_seed_elements(phyl_data, cfg["style"])
    scene = scene.add_elements(elements)

    # Camera: zoom out from close-up to full pattern
    max_extent = compute_max_extent(phyl_data.seeds)
    scene_min = min(w, h)
    full_scale = scene_min / (2.0 * max_extent * cam_cfg["padding"])
    start_scale = full_scale * cam_cfg["start_scale"]
    end_scale = full_scale * cam_cfg["end_scale"]

    scene = scene.animate_camera(
        scale=(start_scale, end_scale),
        easing=easing.out_quad,
    )

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
