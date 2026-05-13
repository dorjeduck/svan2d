"""Double Ring Pendulum Waves — two concentric rings of pendulums.

Usage:
    python showcases/pendulum_waves/double_ring/main.py
"""

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from elements import RingConfig, create_pendulum_elements

from svan2d import Color, ConverterType, VScene, VSceneExporter, configure_logging, easing


def _ring_config(cfg: dict) -> RingConfig:
    return RingConfig(
        count=cfg["count"],
        radius=cfg["radius"],
        arm_length=cfg["arm_length"],
        bob_radius=cfg["bob_radius"],
        max_angle=cfg["max_angle"],
        base_oscillations=cfg["base_oscillations"],
        freq_step=cfg["freq_step"],
        arm_color=cfg["arm_color"],
        arm_width=cfg["arm_width"],
        bob_color_start=Color(cfg["bob_color_start"]),
        bob_color_end=Color(cfg["bob_color_end"]),
        start_angle=cfg.get("start_angle", 180.0),
        clockwise=cfg.get("clockwise", True),
    )


def main():
    configure_logging(level="INFO")

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    scene_cfg = cfg["scene"]
    pendulum_cfg = cfg["pendulum"]
    export_cfg = cfg["export"]

    pendulums = create_pendulum_elements(
        inner=_ring_config(pendulum_cfg["inner"]),
        outer=_ring_config(pendulum_cfg["outer"]),
        quantize_freq=pendulum_cfg.get("quantize_freq", False),
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
