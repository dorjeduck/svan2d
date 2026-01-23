"""Main API for font-to-vertex conversion"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import List, Optional, Union

from svan2d.component.registry import renderer
from svan2d.component.state.base_vertex import VertexState
from svan2d.component.state.state_collection import StateCollectionState
from svan2d.component.vertex.vertex_contours import VertexContours
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D

from .contour_classifier import classify_contours
from .glyph_extractor import FONTTOOLS_AVAILABLE, extract_glyph_outline, load_font


def _transform_contours(
    contours: VertexContours, scale: float, center: bool = True, cursor_x: float = 0.0
) -> VertexContours:
    """Transform contours: scale and optionally center.

    Creates new VertexContours with transformed vertices (Point2D is immutable).
    Position is NOT baked in - that's handled by the state's pos field during rendering.

    Args:
        contours: Source contours
        scale: Scale factor
        center: If True, center glyph at origin. If False, position at cursor_x for text layout.
        cursor_x: X position for text layout (only used when center=False)
    """
    from svan2d.component.vertex.vertex_loop import VertexLoop

    if center:
        # Center at origin (for single letters)
        centroid = contours.centroid()
        offset_x = -centroid.x
        offset_y = -centroid.y
    else:
        # Text layout: position glyph at cursor_x, baseline at y=0
        offset_x = 0
        offset_y = 0

    def transform_vertices(vertices):
        """Scale vertices and translate.

        Note: Y is flipped because font coordinates have Y pointing up,
        while SVG/screen coordinates have Y pointing down.
        """
        result = []
        for v in vertices:
            if center:
                new_x = (v.x + offset_x) * scale
                new_y = -(v.y + offset_y) * scale
            else:
                # For text: glyph origin at cursor_x, scale from there
                new_x = v.x * scale + cursor_x
                new_y = -v.y * scale  # Flip Y, baseline at y=0
            result.append(Point2D(new_x, new_y))
        return result

    # Transform outer contour
    new_outer_vertices = transform_vertices(contours.outer.vertices)
    new_outer = VertexLoop(new_outer_vertices, closed=contours.outer.closed)

    # Transform holes
    new_holes = None
    if contours.has_holes:
        new_holes = []
        for hole in contours.holes:
            new_hole_vertices = transform_vertices(hole.vertices)
            new_holes.append(VertexLoop(new_hole_vertices, closed=hole.closed))

    return VertexContours(new_outer, new_holes)


def _offset_contours(
    contours: VertexContours, offset_x: float, offset_y: float
) -> VertexContours:
    """Offset all vertices in contours by (offset_x, offset_y)."""
    from svan2d.component.vertex.vertex_loop import VertexLoop

    new_outer_vertices = [
        Point2D(v.x + offset_x, v.y + offset_y) for v in contours.outer.vertices
    ]
    new_outer = VertexLoop(new_outer_vertices, closed=contours.outer.closed)

    new_holes = None
    if contours.has_holes:
        new_holes = []
        for hole in contours.holes:
            new_hole_vertices = [
                Point2D(v.x + offset_x, v.y + offset_y) for v in hole.vertices
            ]
            new_holes.append(VertexLoop(new_hole_vertices, closed=hole.closed))

    return VertexContours(new_outer, new_holes)


def _get_glyph_renderer():
    from svan2d.component.renderer.base_vertex import VertexRenderer

    return VertexRenderer


@renderer(_get_glyph_renderer)
@dataclass(frozen=True)
class GlyphState(VertexState):
    """State for a single glyph contour (one connected component).

    Unlike other VertexState subclasses that generate their geometry,
    GlyphState holds pre-computed VertexContours from font extraction.
    """

    _contours: Optional[VertexContours] = None

    def need_morph(self, state) -> bool:
        """Always morph between glyphs since they have different contours."""
        # Different glyph characters always need morphing even though same type
        return True

    def _generate_contours(self) -> VertexContours:
        """Return the pre-computed contours."""
        if self._contours is None:
            raise ValueError(
                "GlyphState has no contours. Use FontGlyphs.get_state() to create."
            )
        return self._contours


class FontGlyphs:
    """Load a font and extract glyph vertices for morphing.

    Example:
        font = FontGlyphs("Helvetica.ttf")
        letter_a = font.get_state("A", num_vertices=128)
        word_cat = font.get_word("CAT", num_vertices=128, spacing=50)
    """

    def __init__(self, font_path: str):
        """Load a font file.

        Args:
            font_path: Path to TTF or OTF font file
        """
        if not FONTTOOLS_AVAILABLE:
            raise ImportError(
                "fonttools is required for font processing. "
                "Install it with: pip install fonttools"
            )
        self._font = load_font(font_path)
        self._font_path = font_path

        # Cache glyph metrics for layout
        self._units_per_em = self._font["head"].unitsPerEm

    def _resolve_scale(self, height: Optional[float], scale: Optional[float]) -> float:
        """Resolve scale from height or scale parameter.

        Args:
            height: Desired height in scene units (takes precedence)
            scale: Direct scale factor

        Returns:
            Scale factor to use
        """
        if height is not None:
            # Calculate scale from desired height
            # Capital letters are typically ~70% of em height
            return height / (self._units_per_em * 0.7)
        elif scale is not None:
            return scale
        else:
            # Default: 50 units tall
            return 50 / (self._units_per_em * 0.7)

    def get_state(
        self,
        char: str,
        num_vertices: int | None = None,
        height: float | None = None,
        scale: float | None = None,
        pos: Point2D | None = None,
        fill_color: Optional[Color] = None,
        stroke_color: Optional[Color] = None,
        stroke_width: float = 0.0,
        _center: bool = True,
        _cursor_x: float = 0.0,
    ) -> StateCollectionState:
        """Get a StateCollectionState for a single character.

        Multi-part characters (like 'i', 'j') return a StateCollectionState
        with multiple GlyphState objects.

        Args:
            char: Single character to extract
            num_vertices: Vertex count per contour
            height: Desired height in scene units (preferred over scale)
            scale: Direct scale factor (use height instead for intuitive sizing)
            pos: Position offset (default: origin) - applied during rendering
            fill_color: Fill color (default: white)
            stroke_color: Stroke color (default: none)
            stroke_width: Stroke width (default: 0)
            _center: Internal - if True center at origin, if False for text layout
            _cursor_x: Internal - cursor X position for text layout

        Returns:
            StateCollectionState containing one GlyphState per disconnected component
        """
        if len(char) != 1:
            raise ValueError(f"Expected single character, got '{char}'")

        # Resolve num_vertices from config if not specified
        if num_vertices is None:
            from svan2d.config import ConfigKey, get_config

            config = get_config()
            num_vertices = config.get(ConfigKey.STATE_VISUAL_NUM_VERTICES, 128)

        assert num_vertices is not None
        # Resolve scale
        resolved_scale = self._resolve_scale(height, scale)

        # Extract glyph outline
        outline = extract_glyph_outline(self._font, char)

        # Classify contours and build VertexContours
        contours_list = classify_contours(outline, num_vertices)

        if not contours_list:
            raise ValueError(f"Character '{char}' has no contours")

        # Default colors
        if fill_color is None:
            fill_color = Color("#ffffff")

        # Default position
        if pos is None:
            pos = Point2D(0, 0)

        # Create GlyphState for each disconnected component
        states = []
        for contours in contours_list:
            # Transform contours (scale and center/position, but NOT pos offset)
            transformed = _transform_contours(
                contours, resolved_scale, center=_center, cursor_x=_cursor_x
            )

            state = GlyphState(
                pos=pos,  # Position applied during rendering via translate transform
                fill_color=fill_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                _num_vertices=num_vertices,
                _contours=transformed,
            )
            states.append(state)

        return StateCollectionState(states=states)

    def get_advance_width(self, char: str) -> float:
        """Get the advance width for a character in font units."""
        outline = extract_glyph_outline(self._font, char)
        return outline.advance_width

    def get_word(
        self,
        text: str,
        num_vertices: int | None = None,
        height: float | None = None,
        scale: float | None = None,
        letter_spacing: float = 1.0,
        pos: Point2D | None = None,
        fill_color: Optional[Color] = None,
        stroke_color: Optional[Color] = None,
        stroke_width: float = 0.0,
    ) -> StateCollectionState:
        """Get a StateCollectionState for a word.

        All character glyphs are flattened into a single StateCollectionState,
        ready for word-to-word morphing.

        Args:
            text: String to convert
            num_vertices: Vertex count per contour
            height: Desired letter height in scene units (preferred over scale)
            scale: Direct scale factor (use height instead for intuitive sizing)
            letter_spacing: Multiplier for space between letters (1.0 = normal, 0.5 = tight)
            pos: Center position (default: origin)
            fill_color: Fill color
            stroke_color: Stroke color
            stroke_width: Stroke width

        Returns:
            StateCollectionState containing all glyph states
        """
        if not text:
            return StateCollectionState(states=[])

        # Resolve num_vertices from config if not specified
        if num_vertices is None:
            from svan2d.config import ConfigKey, get_config

            config = get_config()
            num_vertices = config.get(ConfigKey.STATE_VISUAL_NUM_VERTICES, 128)

        # Resolve scale
        resolved_scale = self._resolve_scale(height, scale)

        target_pos: Point2D = pos if pos is not None else Point2D(0, 0)

        # First pass: collect glyphs with text layout positioning in vertices
        all_glyph_states = []
        cursor_x = 0.0

        for char in text:
            if char == " ":
                space_width = (
                    self.get_advance_width("n") * resolved_scale * letter_spacing
                )
                cursor_x += space_width
                continue

            char_state = self.get_state(
                char=char,
                num_vertices=num_vertices,
                scale=resolved_scale,
                pos=Point2D(0, 0),
                fill_color=fill_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                _center=False,  # Text layout mode
                _cursor_x=cursor_x,
            )
            all_glyph_states.extend(char_state.states)

            advance = self.get_advance_width(char) * resolved_scale * letter_spacing
            cursor_x += advance

        if not all_glyph_states:
            return StateCollectionState(states=[])

        # Calculate word bounding box for centering
        all_vertices = []
        for state in all_glyph_states:
            contours = state._contours
            all_vertices.extend(contours.outer.vertices)
            if contours.has_holes:
                for hole in contours.holes:
                    all_vertices.extend(hole.vertices)

        min_x = min(v.x for v in all_vertices)
        max_x = max(v.x for v in all_vertices)
        min_y = min(v.y for v in all_vertices)
        max_y = max(v.y for v in all_vertices)

        word_center_x = (min_x + max_x) / 2
        word_center_y = (min_y + max_y) / 2

        # Offset to center word at target_pos
        offset_x = target_pos.x - word_center_x
        offset_y = target_pos.y - word_center_y

        # Second pass: for each glyph, center vertices at origin and set pos to actual position
        # This ensures each glyph has a unique pos (required for M→N morphing deduplication)
        final_states = []
        for state in all_glyph_states:
            contours = state._contours

            # Calculate this glyph's centroid
            glyph_centroid = contours.centroid()

            # Center vertices at origin
            centered_contours = _offset_contours(
                contours, -glyph_centroid.x, -glyph_centroid.y
            )

            # Set pos to actual glyph position (centroid + word centering offset)
            glyph_pos = Point2D(
                glyph_centroid.x + offset_x, glyph_centroid.y + offset_y
            )

            new_state = replace(
                state,
                pos=glyph_pos,
                _contours=centered_contours,
            )
            final_states.append(new_state)

        return StateCollectionState(states=final_states)

    def close(self):
        """Close the font file."""
        if self._font is not None:
            self._font.close()
            self._font = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
