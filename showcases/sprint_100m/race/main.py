"""100m Sprint Race Replay — Olympic Finals 2008–2024.

Side-view lane animations of top 3 finishers from 5 Olympic 100m finals,
stacked vertically via VSceneComposite for direct visual comparison.
Race portion plays in real time.
"""

import math
import tomllib
from pathlib import Path

from data_prep import get_all_races, get_max_race_time
from runner_elements import create_runner_elements
from track_elements import create_track_elements

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.vscene.vscene import VScene
from svan2d.vscene.vscene_composite import VSceneComposite
from svan2d.vscene.vscene_exporter import VSceneExporter

configure_logging(level="INFO")

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.toml"
with open(CONFIG_PATH, "rb") as f:
    cfg = tomllib.load(f)


def compute_timing(max_time: float) -> dict:
    """Compute timeline mapping so the race plays in real time.

    Returns dict with:
        race_start: frame_time (0→1) where race begins
        total_duration: total video duration in seconds
        max_time: slowest runner's finish time
        total_frames: number of frames for export
    """
    lead_in = cfg["timing"]["lead_in"]
    hold_after = cfg["timing"]["hold_after"]
    total_duration = lead_in + max_time + hold_after
    framerate = cfg["export"]["framerate"]

    return {
        "race_start": lead_in / total_duration,
        "total_duration": total_duration,
        "max_time": max_time,
        "total_frames": math.ceil(total_duration * framerate),
    }


def create_race_scene(race, timing: dict) -> VScene:
    """Create a VScene for a single race.

    Args:
        race: RaceData for one Olympic final
        timing: Timeline mapping from compute_timing()

    Returns:
        Composed VScene
    """
    scene = VScene(
        width=cfg["scene"]["width"],
        height=cfg["scene"]["height"],
        background=Color(cfg["scene"]["background"]),
    )

    track_elements = create_track_elements(race, timing, cfg)
    scene = scene.add_elements(track_elements)

    circle_elements, label_elements, finish_time_elements = create_runner_elements(
        race, timing, cfg
    )
    scene = scene.add_elements(circle_elements)
    scene = scene.add_elements(label_elements)
    scene = scene.add_elements(finish_time_elements)

    return scene


def main():
    races = get_all_races()
    max_time = get_max_race_time()
    timing = compute_timing(max_time)

    print(
        f"Race duration: {max_time:.2f}s, total video: {timing['total_duration']:.1f}s, "
        f"frames: {timing['total_frames']}"
    )

    scenes: list[VScene] = [create_race_scene(race, timing) for race in races]

    composite = VSceneComposite(
        scenes=list(scenes),  # type: ignore[arg-type]
        direction=cfg["composite"]["direction"],
        gap=cfg["composite"]["gap"],
    )

    exporter = VSceneExporter(
        scene=composite,
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
