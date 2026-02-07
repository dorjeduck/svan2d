"""Typewriter Showcase — characters appear one by one with a blinking cursor.

Usage:
    python showcases/text_animations/typewriter/main.py
"""

import tomllib
from pathlib import Path

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.vscene import VScene, VSceneExporter

from elements import create_char_elements, create_cursor_element, measure_char_width


def main():
    configure_logging(level="INFO")

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    scene_cfg = cfg["scene"]
    font_cfg = cfg["font"]
    text_cfg = cfg["text"]
    anim_cfg = cfg["animation"]
    style_cfg = cfg["style"]
    export_cfg = cfg["export"]

    width = scene_cfg["width"]
    height = scene_cfg["height"]
    font_path = font_cfg["path"]
    font_size = font_cfg["size"]
    lines = text_cfg["lines"]

    typing_ratio = anim_cfg["typing_ratio"]
    line_pause_chars = anim_cfg["line_pause_chars"]
    end_blinks = anim_cfg["end_blinks"]

    text_color = Color(style_cfg["text_color"])
    cursor_color = Color(style_cfg["cursor_color"])
    cursor_width = style_cfg["cursor_width"]
    cursor_height = font_size * style_cfg["cursor_height_ratio"]

    # Measure monospace character width
    char_width = measure_char_width(font_path, font_size)

    # Text layout (center origin)
    padding = 40
    line_height = font_size * 1.4
    margin_x = -width / 2 + padding
    margin_y = -height / 2 + padding + font_size

    # Derive timing from total_frames and framerate
    total_frames = export_cfg["total_frames"]
    framerate = export_cfg["framerate"]
    video_duration = total_frames / framerate

    typing_duration = typing_ratio * video_duration
    end_phase_duration = (1 - typing_ratio) * video_duration

    # Count total character slots (each char = 1 slot, each line pause = N slots)
    num_line_pauses = sum(1 for i in range(1, len(lines)))
    total_char_slots = sum(len(line) for line in lines) + line_pause_chars * num_line_pauses
    char_interval = typing_duration / total_char_slots if total_char_slots > 0 else 0

    # Build character timeline in real seconds
    char_timeline: list[tuple[float, int, int]] = []
    current_sec = 0.0

    for line_idx, line in enumerate(lines):
        if line_idx > 0:
            current_sec += char_interval * line_pause_chars
        for char_idx, ch in enumerate(line):
            if ch == " ":
                current_sec += char_interval
                continue
            char_timeline.append((current_sec, line_idx, char_idx))
            current_sec += char_interval

    # Blink interval derived from end phase
    blink_interval_norm = end_phase_duration / (end_blinks * 2 + 1) / video_duration

    # Normalise to [0, 1]
    char_times = [(t / video_duration, li, ci) for t, li, ci in char_timeline]
    end_time = typing_ratio

    # Create character elements
    char_elements, char_events = create_char_elements(
        lines=lines,
        font_path=font_path,
        font_size=font_size,
        text_color=text_color,
        char_width=char_width,
        margin_x=margin_x,
        margin_y=margin_y,
        line_height=line_height,
        char_times=char_times,
        end_time=1.0,
    )

    # Create cursor element
    cursor_element = create_cursor_element(
        char_events=char_events,
        cursor_color=cursor_color,
        cursor_width=cursor_width,
        cursor_height=cursor_height,
        char_width=char_width,
        blink_interval=blink_interval_norm,
        end_blinks=end_blinks,
        end_time=end_time,
    )

    # Build scene
    scene = VScene(
        width=width,
        height=height,
        background=Color(scene_cfg["background"]),
    )
    scene = scene.add_elements(char_elements)
    scene = scene.add_element(cursor_element)

    # Export
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType(export_cfg["converter"]),
        output_dir=export_cfg["output_dir"],
    )

    exporter.to_mp4(
        filename=export_cfg["filename"],
        total_frames=total_frames,
        framerate=framerate,
        png_width_px=export_cfg["png_width_px"],
    )


if __name__ == "__main__":
    main()
