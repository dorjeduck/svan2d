"""Typewriter animation elements — character VElements + cursor VElement."""

from dataclasses import replace

from svan2d.component.state import TextPathState
from svan2d.component.state.rectangle import RectangleState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.font.glyph_cache import get_glyph_cache
from svan2d.font.glyph_extractor import load_font
from svan2d.velement import VElement


def measure_char_width(font_path: str, font_size: float) -> float:
    """Return the advance width of a single monospace character.

    Measures "M" and uses that for all characters (monospace assumption).
    """
    cache = get_glyph_cache()
    font = load_font(font_path)
    units_per_em = font["head"].unitsPerEm
    scale = font_size / units_per_em
    glyph = cache.get_glyph(font_path, "M", font=font)
    return glyph.advance_width * scale


def create_char_elements(
    lines: list[str],
    font_path: str,
    font_size: float,
    text_color: Color,
    char_width: float,
    margin_x: float,
    margin_y: float,
    line_height: float,
    char_times: list[tuple[float, int, int]],
    end_time: float,
) -> tuple[list[VElement], list[tuple[float, Point2D]]]:
    """Create one VElement per character with instant appear via dual-state keystates.

    Args:
        lines: Text lines to type.
        font_path: Path to monospace font.
        font_size: Font size in px.
        text_color: Fill color for text.
        char_width: Advance width per character.
        margin_x: X offset for first character.
        margin_y: Y offset for first line.
        line_height: Vertical spacing between lines.
        char_times: List of (normalised_time, line_idx, char_idx) for each character.
        end_time: Normalised time when all typing is done.

    Returns:
        (elements, char_events) where char_events is [(time, pos)] for cursor tracking.
    """
    elements: list[VElement] = []
    char_events: list[tuple[float, Point2D]] = []

    for t, line_idx, char_idx in char_times:
        ch = lines[line_idx][char_idx]
        x = margin_x + char_idx * char_width
        y = margin_y + line_idx * line_height
        pos = Point2D(x, y)

        char_events.append((t, pos))

        hidden = TextPathState(
            text=ch,
            font_path=font_path,
            font_size=font_size,
            fill_color=text_color,
            text_anchor="start",
            dominant_baseline="auto",
            pos=pos,
            opacity=0.0,
        )
        visible = replace(hidden, opacity=1.0)

        # Before type_time: invisible
        # At type_time: dual-state [hidden, visible] — incoming=hidden, outgoing=visible
        # After type_time: visible until end
        element = (
            VElement()
            .keystate(hidden, at=0.0)
            .keystate([hidden, visible], at=t, render_index=0)
            .keystate(visible, at=min(end_time, 1.0))
        )
        elements.append(element)

    return elements, char_events


def create_cursor_element(
    char_events: list[tuple[float, Point2D]],
    cursor_color: Color,
    cursor_width: float,
    cursor_height: float,
    char_width: float,
    blink_interval: float,
    end_blinks: int,
    end_time: float,
) -> VElement:
    """Create a blinking cursor that tracks character positions via dual-state keystates.

    Args:
        char_events: [(normalised_time, char_pos)] from create_char_elements.
        cursor_color: Cursor rectangle fill color.
        cursor_width: Cursor width in px.
        cursor_height: Cursor height in px.
        char_width: Character advance width (cursor placed after character).
        blink_interval: Normalised time between blink toggles.
        end_blinks: Number of blink cycles after typing finishes.
        end_time: Normalised time when typing ends.
    """
    if not char_events:
        return VElement(state=RectangleState(opacity=0.0))

    # Initial cursor position: at the position of the first character
    first_pos = char_events[0][1]
    cursor_y_offset = -cursor_height * 0.4  # align with text baseline

    def cursor_pos(char_pos: Point2D) -> Point2D:
        """Cursor sits to the right of the character position."""
        return Point2D(char_pos.x + char_width, char_pos.y + cursor_y_offset)

    def make_state(pos: Point2D, opacity: float) -> RectangleState:
        return RectangleState(
            width=cursor_width,
            height=cursor_height,
            fill_color=cursor_color,
            stroke_color=Color.NONE,
            pos=pos,
            opacity=opacity,
        )

    # Build timeline of keystate events
    # We collect (time, pos, opacity) tuples, then convert to keystates
    events: list[tuple[float, Point2D, float]] = []

    # Start: cursor visible at first char position
    start_pos = cursor_pos(first_pos)
    events.append((0.0, start_pos, 1.0))

    # For each character typed, add blinks between events then jump cursor
    prev_time = 0.0
    prev_pos = start_pos

    for evt_time, char_pos in char_events:
        new_pos = cursor_pos(char_pos)
        gap = evt_time - prev_time

        # Add blinks in the gap
        if gap > blink_interval * 1.5:
            blink_t = prev_time + blink_interval
            visible = True
            while blink_t < evt_time - blink_interval * 0.5:
                visible = not visible
                events.append((blink_t, prev_pos, 0.0 if not visible else 1.0))
                blink_t += blink_interval

        # Cursor jumps to new position (visible)
        events.append((evt_time, new_pos, 1.0))
        prev_time = evt_time
        prev_pos = new_pos

    # After typing: blink at final position, then fade out
    final_pos = prev_pos
    blink_t = end_time
    for i in range(end_blinks * 2):
        opacity = 0.0 if i % 2 == 0 else 1.0
        if blink_t < 1.0:
            events.append((blink_t, final_pos, opacity))
        blink_t += blink_interval

    # Final: fade out
    fade_t = min(blink_t, 1.0)
    events.append((fade_t, final_pos, 0.0))

    # Sort and deduplicate by time
    events.sort(key=lambda e: e[0])

    # Build VElement with dual-state keystates for instant switches
    first_t, first_pos, first_opacity = events[0]
    builder = VElement().keystate(make_state(first_pos, first_opacity), at=min(first_t, 1.0))
    prev_event = events[0]

    for t, pos, opacity in events[1:]:
        t = min(t, 1.0)
        state = make_state(pos, opacity)

        # Skip if time too close to previous (avoid duplicate keystate times)
        if abs(t - prev_event[0]) < 1e-6:
            continue

        # Use dual-state for instant switch:
        # incoming state = what the previous segment interpolates toward
        # outgoing state = what the next segment starts from
        incoming = make_state(prev_event[1], prev_event[2])

        # If position or opacity changed, use dual-state
        if pos != prev_event[1] or opacity != prev_event[2]:
            builder = builder.keystate([incoming, state], at=t, render_index=1)
        else:
            builder = builder.keystate(state, at=t)

        prev_event = (t, pos, opacity)

    return builder
