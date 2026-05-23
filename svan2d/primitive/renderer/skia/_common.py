"""Shared helpers for the per-primitive Skia renderers.

These mirror small pieces of drawsvg renderer behaviour (line caps/joins, dash
parsing, rect/polygon drawing, SVG-path conversion) and are reused across the
individual renderer files in this submodule.
"""

from __future__ import annotations

import skia

from svan2d.path.commands import ClosePath, CubicBezier, MoveTo
from svan2d.path.svg_path import SVGPath
from svan2d.skia.base import SkiaRenderer

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
