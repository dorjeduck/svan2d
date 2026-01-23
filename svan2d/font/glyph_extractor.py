"""Extract bezier paths from font glyphs using fonttools"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, NamedTuple, Optional, Tuple

from svan2d.core.point2d import Point2D, Points2D

try:
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.ttLib import TTFont

    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False


class BezierSegment(NamedTuple):
    """A single bezier segment"""

    type: str  # 'line', 'qcurve', 'curve'
    points: List[Point2D]  # Control points (including end point)


@dataclass
class GlyphContour:
    """A single contour from a glyph (list of bezier segments)"""

    segments: List[BezierSegment]

    def is_empty(self) -> bool:
        return len(self.segments) == 0


@dataclass
class GlyphOutline:
    """All contours from a glyph"""

    contours: List[GlyphContour]
    advance_width: float
    bounds: Optional[Tuple[float, float, float, float]]  # xMin, yMin, xMax, yMax

    def is_empty(self) -> bool:
        return len(self.contours) == 0 or all(c.is_empty() for c in self.contours)


def _check_fonttools():
    if not FONTTOOLS_AVAILABLE:
        raise ImportError(
            "fonttools is required for font processing. "
            "Install it with: pip install fonttools"
        )


def load_font(font_path: str) -> TTFont:
    """Load a font file.

    Args:
        font_path: Path to TTF or OTF font file

    Returns:
        TTFont object
    """
    _check_fonttools()
    return TTFont(font_path)  # type: ignore[reportPossiblyUnboundVariable]


def get_glyph_name(font: TTFont, char: str) -> Optional[str]:
    """Get the glyph name for a character.

    Args:
        font: TTFont object
        char: Single character

    Returns:
        Glyph name or None if not found
    """
    cmap = font.getBestCmap()
    if cmap is None:
        return None
    codepoint = ord(char)
    return cmap.get(codepoint)


def extract_glyph_outline(font: TTFont, char: str) -> GlyphOutline:
    """Extract bezier paths from a glyph.

    Args:
        font: TTFont object
        char: Single character to extract

    Returns:
        GlyphOutline with all contours
    """
    _check_fonttools()

    glyph_name = get_glyph_name(font, char)
    if glyph_name is None:
        raise ValueError(f"Character '{char}' not found in font")

    glyph_set = font.getGlyphSet()
    glyph = glyph_set[glyph_name]

    # Get advance width
    hmtx = font["hmtx"]
    advance_width, _ = hmtx[glyph_name]

    # Get bounds if available
    bounds = None
    if "glyf" in font:
        glyf_table = font["glyf"]
        if glyph_name in glyf_table:
            glyf_glyph = glyf_table[glyph_name]
            if hasattr(glyf_glyph, "xMin") and glyf_glyph.numberOfContours != 0:
                bounds = (glyf_glyph.xMin, glyf_glyph.yMin, glyf_glyph.xMax, glyf_glyph.yMax)

    # Use RecordingPen to capture the drawing commands
    pen = RecordingPen()  # type: ignore[reportPossiblyUnboundVariable]
    glyph.draw(pen)

    # Convert recording to contours
    contours = _recording_to_contours(pen.value)

    return GlyphOutline(contours=contours, advance_width=advance_width, bounds=bounds)


def _recording_to_contours(recording: List) -> List[GlyphContour]:
    """Convert RecordingPen output to GlyphContours.

    RecordingPen records operations as tuples: (operation_name, args)
    """
    contours = []
    current_segments = []
    current_pos = Point2D(0, 0)
    contour_start = Point2D(0, 0)  # Track where the contour started for closePath

    for operation, args in recording:
        if operation == "moveTo":
            # Start of new contour
            if current_segments:
                contours.append(GlyphContour(segments=current_segments))
                current_segments = []
            current_pos = Point2D(args[0][0], args[0][1])
            contour_start = current_pos  # Remember start for close

        elif operation == "lineTo":
            end = Point2D(args[0][0], args[0][1])
            current_segments.append(BezierSegment(type="line", points=[end]))
            current_pos = end

        elif operation == "qCurveTo":
            # Quadratic bezier - args are control points ending with on-curve point
            # fonttools may give multiple control points for TrueType curves
            points = [Point2D(p[0], p[1]) for p in args]

            # Handle implicit on-curve points in TrueType quadratics
            if len(points) == 1:
                # Single point = simple quadratic (control + end)
                current_segments.append(BezierSegment(type="qcurve", points=points))
                current_pos = points[-1]
            else:
                # Multiple off-curve points with implicit on-curve between them
                # Split into individual quadratics
                for i in range(len(points) - 1):
                    ctrl = points[i]
                    if i == len(points) - 2:
                        # Last segment ends at explicit on-curve point
                        end = points[-1]
                    else:
                        # Implicit on-curve point between two off-curve points
                        next_ctrl = points[i + 1]
                        end = Point2D((ctrl.x + next_ctrl.x) / 2, (ctrl.y + next_ctrl.y) / 2)
                    current_segments.append(BezierSegment(type="qcurve", points=[ctrl, end]))
                    current_pos = end

        elif operation == "curveTo":
            # Cubic bezier - args are (ctrl1, ctrl2, end)
            points = [Point2D(p[0], p[1]) for p in args]
            current_segments.append(BezierSegment(type="curve", points=points))
            current_pos = points[-1]

        elif operation == "closePath":
            # Close current contour - add implicit closing line if needed
            if current_segments:
                # Add closing line segment back to start if not already there
                if current_pos.x != contour_start.x or current_pos.y != contour_start.y:
                    current_segments.append(BezierSegment(type="line", points=[contour_start]))
                contours.append(GlyphContour(segments=current_segments))
                current_segments = []

        elif operation == "endPath":
            # End open path (shouldn't happen for closed glyphs)
            if current_segments:
                contours.append(GlyphContour(segments=current_segments))
                current_segments = []

    # Handle any remaining segments
    if current_segments:
        contours.append(GlyphContour(segments=current_segments))

    return contours
