"""Skia renderer for RadialSegmentsState — faithful mirror of RadialSegmentsRenderer."""

from __future__ import annotations

import math

from svan2d.primitive.state.radial_segments import RadialSegmentsState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class RadialSegmentsSkiaRenderer(SkiaRenderer):
    """Radial line segments from the origin at given angles.

    Mirrors RadialSegmentsRenderer: 0° = East, CCW positive; local Y negated
    (Y-up → Y-down). segments may be shared across angles, per-angle, or
    transformed by segments_fn.
    """

    def draw_core(self, canvas, state: RadialSegmentsState, ctx: SkiaContext) -> None:
        stroke = self.stroke_paint(state)
        if stroke is None:
            return

        if state.angles is not None:
            angles = state.angles[: state.num_lines]
        else:
            angles = [i * 360 / state.num_lines for i in range(state.num_lines)]

        segments = state.segments
        for idx, angle in enumerate(angles):
            rad = math.radians(angle)
            base_segments = self._base_segments(segments, idx)
            segs = state.segments_fn(idx, base_segments) if state.segments_fn else base_segments
            if not segs:
                continue
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            for from_px, to_px in segs:
                canvas.drawLine(
                    from_px * cos_a, -from_px * sin_a,
                    to_px * cos_a, -to_px * sin_a,
                    stroke,
                )

    @staticmethod
    def _base_segments(segments, idx):
        if not isinstance(segments, list) or not segments:
            return []
        first = segments[0]
        if isinstance(first, (tuple, list)) and isinstance(first[0], (int, float)):
            return segments  # shared (from_px, to_px) pairs
        if isinstance(first, list):
            return segments[idx] if idx < len(segments) else []  # per-angle
        return []
