"""Convert glyph outlines to SVG path strings."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .glyph_extractor import GlyphContour, GlyphOutline


def glyph_outline_to_svg_path(
    outline: "GlyphOutline",
    scale: float = 1.0,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    flip_y: bool = True,
) -> str:
    """Convert a GlyphOutline to an SVG path string.

    Args:
        outline: GlyphOutline from glyph_extractor
        scale: Scale factor to apply
        offset_x: X offset to apply after scaling
        offset_y: Y offset to apply after scaling
        flip_y: If True, flip Y axis (font coords have Y up, SVG has Y down)

    Returns:
        SVG path data string (d attribute)
    """
    if outline.is_empty():
        return ""

    path_parts = []

    for contour in outline.contours:
        contour_path = _contour_to_svg_path(
            contour, scale, offset_x, offset_y, flip_y
        )
        if contour_path:
            path_parts.append(contour_path)

    return " ".join(path_parts)


def _contour_to_svg_path(
    contour: "GlyphContour",
    scale: float,
    offset_x: float,
    offset_y: float,
    flip_y: bool,
) -> str:
    """Convert a single contour to SVG path commands."""
    if contour.is_empty():
        return ""

    def tx(x: float) -> float:
        return x * scale + offset_x

    def ty(y: float) -> float:
        if flip_y:
            return -y * scale + offset_y
        return y * scale + offset_y

    commands = []

    # For the first segment, we need a starting point
    # The contour starts at the point BEFORE the first segment
    # We'll compute it from the last segment's endpoint (since contours are closed)
    if contour.segments:
        last_seg = contour.segments[-1]
        start_point = last_seg.points[-1]
        commands.append(f"M {tx(start_point.x):.3f} {ty(start_point.y):.3f}")

    for segment in contour.segments:
        if segment.type == "line":
            end = segment.points[0]
            commands.append(f"L {tx(end.x):.3f} {ty(end.y):.3f}")

        elif segment.type == "qcurve":
            if len(segment.points) == 1:
                # Single point means it's the end point of a degenerate quadratic
                end = segment.points[0]
                commands.append(f"L {tx(end.x):.3f} {ty(end.y):.3f}")
            elif len(segment.points) == 2:
                ctrl, end = segment.points
                commands.append(
                    f"Q {tx(ctrl.x):.3f} {ty(ctrl.y):.3f} "
                    f"{tx(end.x):.3f} {ty(end.y):.3f}"
                )
            else:
                # Multiple control points - should have been split in extractor
                # but handle gracefully
                for i in range(0, len(segment.points) - 1, 2):
                    ctrl = segment.points[i]
                    end = segment.points[i + 1] if i + 1 < len(segment.points) else segment.points[-1]
                    commands.append(
                        f"Q {tx(ctrl.x):.3f} {ty(ctrl.y):.3f} "
                        f"{tx(end.x):.3f} {ty(end.y):.3f}"
                    )

        elif segment.type == "curve":
            if len(segment.points) == 3:
                ctrl1, ctrl2, end = segment.points
                commands.append(
                    f"C {tx(ctrl1.x):.3f} {ty(ctrl1.y):.3f} "
                    f"{tx(ctrl2.x):.3f} {ty(ctrl2.y):.3f} "
                    f"{tx(end.x):.3f} {ty(end.y):.3f}"
                )
            else:
                # Fallback for unexpected point count
                end = segment.points[-1]
                commands.append(f"L {tx(end.x):.3f} {ty(end.y):.3f}")

    # Close the path
    commands.append("Z")

    return " ".join(commands)
