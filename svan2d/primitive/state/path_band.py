from __future__ import annotations

from dataclasses import dataclass, field

from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.primitive.registry import renderer
from svan2d.primitive.renderer.path_band import PathBandRenderer
from svan2d.primitive.state.base_color import ColorState
from svan2d.primitive.state.path import StrokeLinecap, StrokeLinejoin


Segment = tuple[Point2D, Point2D]


@renderer(PathBandRenderer)
@dataclass(frozen=True)
class PathBandState(ColorState):
    """State holding N line segments rendered as one group with per-segment
    stroke styling. Collapses what would otherwise be N separate VElements
    (one per segment) into a single element.

    `stroke_opacities` and `stroke_widths`, when provided, override the
    shared `stroke_opacity` / `stroke_width` on a per-segment basis. They
    must match `len(segments)` when provided.
    """

    segments: tuple[Segment, ...] = field(default_factory=tuple)
    stroke_opacities: tuple[float, ...] | None = None
    stroke_widths: tuple[float, ...] | None = None
    stroke_colors: tuple[Color, ...] | None = None

    stroke_linecap: StrokeLinecap | str = StrokeLinecap.BUTT
    stroke_linejoin: StrokeLinejoin | str = StrokeLinejoin.MITER

    NON_INTERPOLATABLE_FIELDS = frozenset(
        [
            "NON_INTERPOLATABLE_FIELDS",
            "segments",
            "stroke_opacities",
            "stroke_widths",
            "stroke_colors",
        ]
    )

    def __post_init__(self):
        super().__post_init__()

        if not isinstance(self.segments, tuple):
            self._set_field("segments", tuple(self.segments))
        if self.stroke_opacities is not None and not isinstance(self.stroke_opacities, tuple):
            self._set_field("stroke_opacities", tuple(self.stroke_opacities))
        if self.stroke_widths is not None and not isinstance(self.stroke_widths, tuple):
            self._set_field("stroke_widths", tuple(self.stroke_widths))
        if self.stroke_colors is not None and not isinstance(self.stroke_colors, tuple):
            self._set_field("stroke_colors", tuple(self.stroke_colors))

        n = len(self.segments)
        if self.stroke_opacities is not None and len(self.stroke_opacities) != n:
            raise ValueError(
                f"stroke_opacities length {len(self.stroke_opacities)} != segments length {n}"
            )
        if self.stroke_widths is not None and len(self.stroke_widths) != n:
            raise ValueError(
                f"stroke_widths length {len(self.stroke_widths)} != segments length {n}"
            )
        if self.stroke_colors is not None and len(self.stroke_colors) != n:
            raise ValueError(
                f"stroke_colors length {len(self.stroke_colors)} != segments length {n}"
            )
