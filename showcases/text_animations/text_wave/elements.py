"""Element construction for the text wave showcase."""

import math
from dataclasses import replace

from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.font.font_glyphs import FontGlyphs
from svan2d.velement import VElement


def create_wave_elements(
    font: FontGlyphs,
    text: str,
    font_size: float,
    color: Color,
    scene_width: float,
    amplitude: float,
    wavelength: float,
    speed: float,
    entry_duration: float,
    stagger: float,
    total_frames: int,
    align_rotation: bool = True,
    decay_start: float = 1.0,
    decay_end: float = 1.0,
) -> list[VElement]:
    """Build one VElement per non-space letter with pre-computed keystates.

    Returns:
        List of VElement instances ready to add to a VScene.
    """
    # --- Per-character base states (baseline-aligned via get_letters) ---
    base_states = font.get_letters(
        text, height=font_size, fill_color=color
    )

    # Each letter's resting screen-x is encoded in its inner glyph positions.
    # The outer StateCollectionState.pos acts as a *displacement* on top.
    # Extract the resting x from the first glyph part of each letter.
    rest_xs = [s.states[0].pos.x for s in base_states]

    # --- Wave helpers ---
    k = 2 * math.pi / wavelength
    decay_range = decay_end - decay_start

    def amplitude_at(t: float) -> float:
        if t <= decay_start:
            return amplitude
        if t >= decay_end:
            return 0.0
        progress = (t - decay_start) / decay_range
        return amplitude * 0.5 * (1.0 + math.cos(math.pi * progress))

    def wave_y(x: float, phase: float, amp: float) -> float:
        return amp * math.sin(k * x + phase)

    def wave_rotation(x: float, phase: float, amp: float) -> float:
        slope = amp * k * math.cos(k * x + phase)
        return math.degrees(math.atan(slope))

    # --- Build keystates per letter ---
    offscreen_x = scene_width / 2 + 50

    elements = []
    for letter_idx, (base_state, rest_x) in enumerate(
        zip(base_states, rest_xs)
    ):
        entry_start = letter_idx * stagger
        arrival_t = entry_start + entry_duration

        frame_states = []
        frame_times = []

        for frame in range(total_frames):
            t = frame / (total_frames - 1)
            phase = speed * 2 * math.pi * t

            # Compute absolute screen-x for wave function
            if t < entry_start:
                screen_x = offscreen_x
            elif t < arrival_t:
                progress = (t - entry_start) / entry_duration
                screen_x = offscreen_x + (rest_x - offscreen_x) * progress
            else:
                screen_x = rest_x

            amp = amplitude_at(t)
            if amp == 0.0:
                y = 0.0
                rot = 0.0
            else:
                y = wave_y(screen_x, phase, amp)
                rot = wave_rotation(screen_x, phase, amp) if align_rotation else 0.0

            # pos is a displacement from the letter's resting position.
            # Rotation must be set on each inner GlyphState (which has vertices
            # centered at its own origin) so it pivots around the glyph center.
            dx = screen_x - rest_x
            inner = [replace(s, rotation=rot) for s in base_state.states]
            state = replace(base_state, pos=Point2D(dx, y), states=inner)
            frame_states.append(state)
            frame_times.append(t)

        elements.append(VElement().keystates(frame_states, at=frame_times))

    return elements
