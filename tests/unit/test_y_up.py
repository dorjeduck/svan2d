"""Y-up geometry: `pos` is always Y-up (the renderer negates pos.y), but a
state's own geometry (path data, vertices, raw-svg coordinates) defaults to
SVG-native Y-down so glyph/shape outlines render upright. `y_up=True` opts a
state's geometry into the same Y-up world frame as `pos`.
"""

from svan2d.core import Color, Point2D
from svan2d.primitive import (
    CircleRenderer,
    CircleState,
    PathRenderer,
    PathState,
    RawSvgRenderer,
    RawSvgState,
)


def test_y_up_appends_reflection_to_transform():
    """y_up adds a trailing scale(1,-1) (innermost → applied to geometry
    first); default geometry gets no reflection."""
    up = PathState(data="M 0,300 L 100,300", stroke_color=Color("#fff"), y_up=True)
    assert PathRenderer._build_transform_string(up) == "scale(1,-1)"

    down = PathState(data="M 0,300 L 100,300", stroke_color=Color("#fff"))
    assert PathRenderer._build_transform_string(down) is None


def test_y_up_reflection_is_innermost_with_pos():
    """With a non-zero pos the reflection is rightmost so the geometry flips
    before pos translates — mapping geometry (gx, gy) to world (pos + g)."""
    s = PathState(
        data="M 0,0", pos=Point2D(10, 20), stroke_color=Color("#fff"), y_up=True
    )
    # pos.y negated by translate; reflection trails.
    assert PathRenderer._build_transform_string(s) == "translate(10,-20) scale(1,-1)"


def test_y_up_geometry_matches_pos_placed_element():
    """A y_up path vertex and a pos-placed circle at the same world point land
    at the same screen coordinates."""
    circle = CircleState(pos=Point2D(0, 120), radius=4)
    c_t = CircleRenderer._build_transform_string(circle)  # translate(0,-120)
    # The path reflects (0,120) -> (0,-120): same screen Y as the circle.
    assert "translate(0,-120)" == c_t
    path = PathState(data="M 0,120", y_up=True, stroke_color=Color("#fff"))
    assert PathRenderer._build_transform_string(path) == "scale(1,-1)"
    # (scale(1,-1) maps the literal vertex 0,120 to 0,-120 — the circle's Y.)


def test_raw_svg_counter_flips_text_and_image_only():
    """y_up RawSvg leaves geometry (it flips with the group) but wraps
    text/image in a local reflection so they stay upright."""
    raw = (
        '<path d="M 0,300 L 100,300" stroke="red"/>'
        '<text x="10" y="300">HI</text>'
        '<image x="5" y="100" width="40" height="60"/>'
    )
    out = RawSvgRenderer()._render_core(RawSvgState(svg_data=raw, y_up=True))
    svg = out.content if hasattr(out, "content") else str(out)
    # path untouched
    assert '<path d="M 0,300 L 100,300" stroke="red"' in svg
    # text reflected about its baseline y=300 -> translate(0,600)
    assert 'transform="translate(0,600.0) scale(1,-1)"' in svg
    assert "<text" in svg
    # image reflected about its centre y+h/2 = 130 -> translate(0,260)
    assert 'transform="translate(0,260.0) scale(1,-1)"' in svg


def test_raw_svg_unchanged_when_not_y_up():
    raw = '<text x="0" y="0">x</text>'
    out = RawSvgRenderer()._render_core(RawSvgState(svg_data=raw))
    svg = out.content if hasattr(out, "content") else str(out)
    assert "scale(1,-1)" not in svg
