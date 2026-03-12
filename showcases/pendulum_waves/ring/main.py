"""Ring Pendulum Waves — pendulums arranged in a ring, swinging radially outward.

Usage:
    python showcases/pendulum_waves/ring/main.py
"""

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from elements import create_pendulum_elements

from svan2d import Color, ConverterType, VScene, VSceneExporter, configure_logging, easing


def main():
    configure_logging(level="INFO")

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    scene_cfg = cfg["scene"]
    pendulum_cfg = cfg["pendulum"]
    export_cfg = cfg["export"]

    pendulums = create_pendulum_elements(
        count=pendulum_cfg["count"],
        circle_radius=pendulum_cfg["circle_radius"],
        arm_length=pendulum_cfg["arm_length"],
        bob_radius=pendulum_cfg["bob_radius"],
        max_angle=pendulum_cfg["max_angle"],
        base_oscillations=pendulum_cfg["base_oscillations"],
        freq_step=pendulum_cfg["freq_step"],
        arm_color=pendulum_cfg["arm_color"],
        arm_width=pendulum_cfg["arm_width"],
        bob_color_start=Color(pendulum_cfg["bob_color_start"]),
        bob_color_end=Color(pendulum_cfg["bob_color_end"]),
        quantize_freq=pendulum_cfg.get("quantize_freq", False),
        start_angle=pendulum_cfg.get("start_angle", 180.0),
        clockwise=pendulum_cfg.get("clockwise", True),
    )

    easing_name = scene_cfg.get("timeline_easing", "")
    timeline_easing = getattr(easing, easing_name) if easing_name else None

    scene = VScene(
        width=scene_cfg["width"],
        height=scene_cfg["height"],
        background=Color(scene_cfg["background"]),
        timeline_easing=timeline_easing,
        reverse=scene_cfg.get("reverse", False),
    )
    scene = scene.add_elements(pendulums)

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
        num_thumbnails=100
    )
    


if __name__ == "__main__":
    main()
