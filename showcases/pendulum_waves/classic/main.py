"""Pendulum Waves — phase-shifted pendulums creating optical illusion patterns.

15 pendulums swing with slightly different frequencies, creating mesmerizing
traveling wave and convergence patterns. All motion is defined declaratively
via custom interpolation functions — no per-frame logic.

Features demonstrated:
- interpolation_dict: custom Point2D interpolation for bob positions
- state_interpolation: full state computation for arm elements
- Color.lerp: smooth color gradient across the pendulum row

Usage:
    python showcases/pendulum_waves/classic/main.py
"""

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from elements import create_pendulum_elements, create_support_bar

from svan2d import (
    Color,
    ConverterType,
    VScene,
    VSceneExporter,
    configure_logging,
    easing,
)


def main():
    configure_logging(level="INFO")

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    scene_cfg = cfg["scene"]
    pendulum_cfg = cfg["pendulum"]
    bar_cfg = cfg["bar"]
    export_cfg = cfg["export"]

    count = pendulum_cfg["count"]
    spacing = pendulum_cfg["spacing"]

    # Support bar spans the full row plus some padding
    bar_width = (count - 1) * spacing + 60
    bar = create_support_bar(
        center_y=pendulum_cfg["pivot_y"],
        width=bar_width,
        color=bar_cfg["color"],
        stroke_width=bar_cfg["width"],
    )

    # Pendulums
    pendulums = create_pendulum_elements(
        count=count,
        pivot_y=pendulum_cfg["pivot_y"],
        arm_length=pendulum_cfg["arm_length"],
        bob_radius=pendulum_cfg["bob_radius"],
        max_angle=pendulum_cfg["max_angle"],
        base_oscillations=pendulum_cfg["base_oscillations"],
        freq_step=pendulum_cfg["freq_step"],
        spacing=spacing,
        arm_color=pendulum_cfg["arm_color"],
        arm_width=pendulum_cfg["arm_width"],
        bob_color_start=Color(pendulum_cfg["bob_color_start"]),
        bob_color_end=Color(pendulum_cfg["bob_color_end"]),
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
    scene = scene.add_element(bar)
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
        num_thumbnails=100,
    )


if __name__ == "__main__":
    main()
