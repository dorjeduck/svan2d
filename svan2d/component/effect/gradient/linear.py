"""Linear gradient implementation"""

from __future__ import annotations
from dataclasses import dataclass

import drawsvg as dw

from svan2d.core.point2d import Point2D

from .base import Gradient
from .gradient_stop import GradientStop


@dataclass(frozen=True)
class LinearGradient(Gradient):
    """Linear gradient between two points

    Args:
        x1, y1: Start point coordinates
        x2, y2: End point coordinates
        stops: Tuple of GradientStop defining color transitions
    """

    start: Point2D
    end: Point2D
    stops: tuple[GradientStop, ...]

    def __post_init__(self):
        if len(self.stops) < 2:
            raise ValueError(
                f"Gradient must have at least 2 stops, got {len(self.stops)}"
            )

    def to_drawsvg(self) -> dw.LinearGradient:

        import uuid

        # Generate unique ID
        gradient_id = f"gradient-{uuid.uuid4().hex[:8]}"

        """Convert to drawsvg LinearGradient"""
        grad = dw.LinearGradient(
            self.start.x,
            self.start.y,
            self.end.x,
            self.end.y,
            gradientUnits="userSpaceOnUse",
            id=gradient_id,
        )
        for stop in self.stops:
            grad.add_stop(stop.offset, stop.color.to_hex(), stop.opacity)
        return grad

    def interpolate(self, other: Gradient, t: float) -> Gradient:
        """Interpolate between two LinearGradient instances"""
        if not isinstance(other, LinearGradient) or len(self.stops) != len(other.stops):
            # Step interpolation for different gradient types or mismatched stop counts
            return self if t < 0.5 else other

        # Interpolate position values
        start = self.start.lerp(other.start, t)
        end = self.end.lerp(other.end, t)

        # Interpolate stops
        interpolated_stops = []
        for s1, s2 in zip(self.stops, other.stops):
            offset = s1.offset + (s2.offset - s1.offset) * t
            color = s1.color.interpolate(s2.color, t)
            opacity = s1.opacity + (s2.opacity - s1.opacity) * t
            interpolated_stops.append(GradientStop(offset, color, opacity))

        return LinearGradient(start, end, tuple(interpolated_stops))
