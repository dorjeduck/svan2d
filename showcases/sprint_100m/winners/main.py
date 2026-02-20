"""Olympic 100m Winners Race — Gold Medalists 1988–2024.

Fantasy race pitting all 10 Olympic 100m gold medalists against each other
in a single scene with 10 lanes. Race portion plays in real time using
PCHIP interpolation from actual split data.
"""

import math
import tomllib
from pathlib import Path

from data_prep import get_max_time, get_runners
from runner_elements import create_runner_elements
from track_elements import create_track_elements

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.vscene.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

configure_logging(level="INFO")

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.toml"
with open(CONFIG_PATH, "rb") as f:
    cfg = tomllib.load(f)


def compute_timing(max_time: float) -> dict:
    """Compute timeline mapping so the race plays in real time.

    Returns dict with normalized keypoints and durations for all phases:
        lead_in → race → hold_after → results_transition → results_hold
    """
    lead_in = cfg["timing"]["lead_in"]
    hold_after = cfg["timing"]["hold_after"]
    results_transition = cfg["timing"]["results_transition"]
    results_hold = cfg["timing"]["results_hold"]
    total_duration = lead_in + max_time + hold_after + results_transition + results_hold
    framerate = cfg["export"]["framerate"]

    return {
        "race_start": lead_in / total_duration,
        "results_start": (lead_in + max_time + hold_after) / total_duration,
        "results_end": (lead_in + max_time + hold_after + results_transition)
        / total_duration,
        "total_duration": total_duration,
        "max_time": max_time,
        "total_frames": math.ceil(total_duration * framerate),
    }


def create_scene(runners, timing: dict) -> VScene:
    """Create the single VScene with all 10 runners.

    Args:
        runners: List of 10 RunnerSplitData
        timing: Timeline mapping from compute_timing()

    Returns:
        Composed VScene
    """
    scene = VScene(
        width=cfg["scene"]["width"],
        height=cfg["scene"]["height"],
        background=Color(cfg["scene"]["background"]),
    )

    num_lanes = len(runners)
    max_time = timing["max_time"]

    track_elements = create_track_elements(num_lanes, max_time, timing, cfg)
    scene = scene.add_elements(track_elements)

    circle_elements, label_elements, finish_time_elements, placement_elements = (
        create_runner_elements(runners, timing, cfg)
    )
    scene = scene.add_elements(circle_elements)
    scene = scene.add_elements(label_elements)
    scene = scene.add_elements(finish_time_elements)
    scene = scene.add_elements(placement_elements)

    return scene


def main():
    runners = get_runners()
    max_time = get_max_time()
    timing = compute_timing(max_time)

    print(f"Runners: {len(runners)}")
    print(
        f"Fastest: {min(r.final_time for r in runners):.2f}s (#{next(r.placement for r in runners if r.placement == 1)})"
    )
    print(f"Slowest: {max_time:.2f}s")
    print(
        f"Total video: {timing['total_duration']:.1f}s, frames: {timing['total_frames']}"
    )

    scene = create_scene(runners, timing)

    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType(cfg["export"]["converter"]),
        output_dir=cfg["export"]["output_dir"],
    )

    exporter.to_mp4(
        filename=cfg["export"]["filename"],
        total_frames=timing["total_frames"],
        framerate=cfg["export"]["framerate"],
        png_width_px=cfg["export"]["png_width_px"],
        parallel_workers=(4 if cfg["export"]["converter"] == "playwright_http" else 1),
    )


if __name__ == "__main__":
    main()
