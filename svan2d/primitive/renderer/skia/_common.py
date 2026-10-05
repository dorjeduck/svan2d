"""Shared helpers for the per-primitive Skia renderers.

These mirror small pieces of drawsvg renderer behaviour (line caps/joins, dash
parsing, rect/polygon drawing, SVG-path conversion) and are reused across the
individual renderer files in this submodule.
"""

from __future__ import annotations

import math
import re
import unicodedata

import skia

from svan2d.path.commands import ClosePath, CubicBezier, MoveTo
from svan2d.path.svg_path import SVGPath
from svan2d.skia.base import SkiaContext, SkiaRenderer

_CAP = {
    "butt": skia.Paint.kButt_Cap,
    "round": skia.Paint.kRound_Cap,
    "square": skia.Paint.kSquare_Cap,
}

_JOIN = {
    "miter": skia.Paint.kMiter_Join,
    "round": skia.Paint.kRound_Join,
    "bevel": skia.Paint.kBevel_Join,
}


def svg_whitespace(text: str) -> str:
    """A line of text as SVG lays it out by default (xml:space="default"):
    tabs become spaces, runs of spaces become one, and spaces at either end
    are dropped. Newlines are left alone: drawsvg splits text into lines on
    them before any renderer sees it."""
    return re.sub(r" {2,}", " ", text.replace("\t", " ")).strip(" ")


_ZWJ = "‍"


def _extends(char: str) -> bool:
    """Whether `char` belongs to the cluster before it rather than starting one."""
    cp = ord(char)
    return (
        char == _ZWJ
        or 0xFE00 <= cp <= 0xFE0F  # variation selectors
        or 0x1F3FB <= cp <= 0x1F3FF  # skin tones
        or 0xE0020 <= cp <= 0xE007F  # tags
        or cp == 0x20E3  # keycap
        or unicodedata.combining(char) != 0
    )


def clusters(text: str) -> list[str]:
    """`text` cut where the browser would put a letter-spacing gap: a character
    with its selectors, marks and joined emoji stays one."""
    out: list[str] = []
    for char in text:
        if out and (_extends(char) or out[-1].endswith(_ZWJ)):
            out[-1] += char
        else:
            out.append(char)
    return out


def font_runs(text: str, font: skia.Font, ctx: SkiaContext) -> list[tuple[str, skia.Font]]:
    """`text` in pieces drawn in one font each, in order."""
    runs: list[tuple[str, skia.Font]] = []
    for cluster in clusters(text):
        f = ctx.font_for(cluster, font)
        if runs and runs[-1][1] is f:
            runs[-1] = (runs[-1][0] + cluster, f)
        else:
            runs.append((cluster, f))
    return runs


def anchor_offset(width: float, anchor: str) -> float:
    """Where text `width` wide starts, from its anchor point (SVG
    text-anchor; anything but middle and end anchors at the start)."""
    if anchor == "middle":
        return -width / 2
    if anchor == "end":
        return -width
    return 0.0


def draw_line(canvas, text: str, x: float, y: float, font: skia.Font, paint,
              spacing: float, anchor: str, ctx: SkiaContext) -> None:
    """`text` on a straight baseline at `y`, anchored at `x`, as the browser
    lays out an SVG <text>: spaces collapsed, each piece in the font that has
    it, and with letter-spacing the gap after every glyph — the last one too —
    counted in the width the anchor goes by."""
    text = svg_whitespace(text)
    if spacing:
        glyphs = [(c, ctx.font_for(c, font)) for c in clusters(text)]
        x += anchor_offset(sum(f.measureText(c) + spacing for c, f in glyphs), anchor)
        for c, f in glyphs:
            canvas.drawString(c, x, y, f, paint)
            x += f.measureText(c) + spacing
    else:
        runs = font_runs(text, font, ctx)
        x += anchor_offset(sum(f.measureText(r) for r, f in runs), anchor)
        for r, f in runs:
            canvas.drawString(r, x, y, f, paint)
            x += f.measureText(r)


def draw_along_path(canvas, text: str, start: float, pm: skia.PathMeasure, font: skia.Font,
                    paint, spacing: float, anchor: str, baseline: float,
                    ctx: SkiaContext, flip: bool = False) -> None:
    """`text` along the path `pm` measures, anchored at distance `start`, each
    piece turned to the path where its middle falls; pieces whose middle falls
    off the path are left out, as the browser does. Laid out as `draw_line`."""
    text = svg_whitespace(text)
    length = pm.getLength()
    glyphs = [(c, f, f.measureText(c)) for c in clusters(text) for f in [ctx.font_for(c, font)]]
    cursor = start + anchor_offset(sum(a + spacing for _, _, a in glyphs), anchor)
    for c, f, advance in glyphs:
        mid = cursor + advance / 2
        if 0.0 <= mid <= length:
            pos, tan = pm.getPosTan(mid)
            canvas.save()
            canvas.translate(pos.x(), pos.y())
            canvas.rotate(math.degrees(math.atan2(tan.y(), tan.x())))
            if flip:
                canvas.scale(1.0, -1.0)
            canvas.drawString(c, -advance / 2, baseline, f, paint)
            canvas.restore()
        cursor += advance + spacing


def _parse_dash(spec: str) -> list[float]:
    return [float(v) for v in spec.replace(" ", ",").split(",") if v != ""]


def _draw_rect(r: SkiaRenderer, canvas, state, w, h, corner_radius) -> None:
    rect = skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h)
    radius = min(corner_radius, min(w, h) / 2) if corner_radius > 0 else 0.0
    fill = r.fill_paint(state)
    if fill is not None:
        canvas.drawRoundRect(rect, radius, radius, fill) if radius > 0 else canvas.drawRect(rect, fill)
    stroke = r.stroke_paint(state)
    if stroke is not None:
        canvas.drawRoundRect(rect, radius, radius, stroke) if radius > 0 else canvas.drawRect(rect, stroke)


def _fill_stroke_poly(r: SkiaRenderer, canvas, state, points) -> None:
    """Fill then stroke a closed polygon defined by local points."""
    path = skia.Path()
    path.moveTo(*points[0])
    for p in points[1:]:
        path.lineTo(*p)
    path.close()
    fill = r.fill_paint(state)
    if fill is not None:
        canvas.drawPath(path, fill)
    stroke = r.stroke_paint(state)
    if stroke is not None:
        cap = getattr(state, "stroke_linecap", "") or ""
        stroke.setStrokeCap(_CAP.get(cap, skia.Paint.kButt_Cap))
        canvas.drawPath(path, stroke)


def _svgpath_to_skia(svg_path: SVGPath) -> skia.Path:
    """Build a skia.Path from an SVGPath via its canonical cubic-bezier form."""
    path = skia.Path()
    for cmd in svg_path.to_cubic_beziers().commands:
        if isinstance(cmd, MoveTo):
            path.moveTo(cmd.pos.x, cmd.pos.y)
        elif isinstance(cmd, CubicBezier):
            path.cubicTo(
                cmd.center1.x, cmd.center1.y,
                cmd.center2.x, cmd.center2.y,
                cmd.pos.x, cmd.pos.y,
            )
        elif isinstance(cmd, ClosePath):
            path.close()
    return path


def _add_loop(path: skia.Path, vertices, *, close: bool) -> None:
    if not vertices:
        return
    path.moveTo(vertices[0].x, vertices[0].y)
    for v in vertices[1:]:
        path.lineTo(v.x, v.y)
    if close:
        path.close()


def _is_closed(vertices) -> bool:
    if len(vertices) < 2:
        return False
    return vertices[-1].distance_to(vertices[0]) < 1.0
