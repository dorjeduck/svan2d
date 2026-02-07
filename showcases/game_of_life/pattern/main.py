"""Game of Life pattern showcase.

Displays various Game of Life patterns from simple to complex.
"""

from svan2d.converter.converter_type import ConverterType
from svan2d.core.logger import configure_logging
from svan2d.transition.scene import Fade, Iris, Slide, Wipe, Zoom
from svan2d.vscene.vscene_exporter import VSceneExporter
from svan2d.vscene.vscene_sequence import VSceneSequence

from config import (
    FPS,
    PATTERNS_ENABLED,
    SCENE_HEIGHT,
    SCENE_WIDTH,
    TRANSITION_FRAMES,
    TRANSITION_TYPE,
)
from pattern_scene import create_pattern_scene
from patterns import PATTERNS

configure_logging(level="INFO")

# Filter patterns based on config
ENABLED_PATTERNS = [p for p in PATTERNS if PATTERNS_ENABLED.get(p.name, False)]


def get_transition(total_frames: int):
    """Get transition effect based on config.

    Converts TRANSITION_FRAMES to relative duration.
    """
    rel_duration = TRANSITION_FRAMES / total_frames
    transitions = {
        "fade": Fade(duration=rel_duration),
        "wipe": Wipe(direction="left", duration=rel_duration),
        "slide": Slide(direction="left", duration=rel_duration),
        "zoom": Zoom(duration=rel_duration),
        "iris": Iris(duration=rel_duration),
    }
    return transitions.get(TRANSITION_TYPE, Fade(duration=rel_duration))


def main():
    patterns = ENABLED_PATTERNS

    # Calculate total frames
    scene_frames = sum(int(p.duration * FPS) for p in patterns)
    transition_frames_total = TRANSITION_FRAMES * (len(patterns) - 1)
    total_frames = scene_frames + transition_frames_total
    total_duration = total_frames / FPS

    print(f"Creating {len(patterns)} pattern scenes...")
    print(f"Total: {total_frames} frames ({total_duration:.1f} seconds)")

    # Build sequence
    sequence = VSceneSequence(width=SCENE_WIDTH, height=SCENE_HEIGHT)
    transition = get_transition(total_frames)

    for i, pattern in enumerate(patterns):
        pattern_frames = int(pattern.duration * FPS)
        print(f"  [{i+1}/{len(patterns)}] {pattern.name} ({pattern_frames} frames)")

        scene = create_pattern_scene(pattern)

        # Calculate relative duration (0.0-1.0)
        rel_duration = pattern_frames / total_frames

        sequence = sequence.scene(scene, duration=rel_duration)

        # Add transition (except after last scene)
        if i < len(patterns) - 1:
            sequence = sequence.transition(transition)

    # Export
    exporter = VSceneExporter(
        scene=sequence,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )

    exporter.to_mp4(
        filename="game_of_life_patterns",
        total_frames=total_frames,
        framerate=FPS,
        png_width_px=SCENE_WIDTH,
        num_thumbnails=len(patterns),
        parallel_workers=4,
    )


if __name__ == "__main__":
    main()
