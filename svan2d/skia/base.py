"""Base classes and shared helpers for the Skia rendering backend."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import skia

if TYPE_CHECKING:
    from svan2d.core.color import Color
    from svan2d.primitive.state.base import State


class SkiaUnsupported(Exception):
    """Raised when a state/feature cannot be rendered by the Skia backend.

    Caught by SkiaSvgConverter, which stops with a detailed error (no fallback).
    """


@dataclass
class SkiaContext:
    """Per-render shared state passed to every SkiaRenderer.

    Holds resource caches so repeated renders (animation frames) reuse typefaces
    and decoded images instead of rebuilding them.
    """

    typefaces: dict[tuple[str, int], skia.Typeface] = field(default_factory=dict)
    images: dict[int, skia.Image] = field(default_factory=dict)
    # Scene size in world units; raw_svg uses it as the SVGDOM container size so
    # percentage-based coordinates resolve the same way the SVG backend sees them.
    scene_width: float = 0.0
    scene_height: float = 0.0

    def typeface(self, family: str, weight: str) -> skia.Typeface:
        bold = str(weight).lower() in ("bold", "700", "800", "900")
        key = (family, 1 if bold else 0)
        tf = self.typefaces.get(key)
        if tf is None:
            style = skia.FontStyle.Bold() if bold else skia.FontStyle.Normal()
            tf = skia.Typeface(family, style)
            self.typefaces[key] = tf
        return tf


def skia_color(color: "Color", opacity: float = 1.0) -> int:
    """Convert a svan2d Color (+ extra opacity) to a skia ARGB int."""
    a = max(0, min(255, int(round(255 * opacity))))
    return skia.ColorSetARGB(a, color.r, color.g, color.b)


class SkiaRenderer(ABC):
    """Abstract base for Skia renderers — the canvas analogue of Renderer.

    Subclasses implement draw_core(canvas, state, ctx) drawing the geometry in
    the state's *local* coordinates (origin at 0,0), exactly mirroring the
    drawsvg renderer's _render_core. The base draw() applies transform + opacity.
    """

    def draw(self, canvas: skia.Canvas, state: "State", ctx: SkiaContext) -> None:
        """Apply transform + opacity, then draw the geometry.

        No capability checks here: the scene was validated once up front
        (svan2d.skia.support.check_scene), so the render loop is check-free.
        """
        canvas.save()
        try:
            self._apply_transform(canvas, state)
            opacity = state.opacity if state.opacity is not None else 1.0
            if opacity < 1.0:
                canvas.saveLayerAlpha(None, int(round(opacity * 255)))
                try:
                    self.draw_core(canvas, state, ctx)
                finally:
                    canvas.restore()
            else:
                self.draw_core(canvas, state, ctx)
        finally:
            canvas.restore()

    @staticmethod
    def _apply_transform(canvas: skia.Canvas, state: "State") -> None:
        """Mirror Renderer._build_transform_string as skia canvas ops.

        SVG list order is "translate rotate scale skewX skewY [scale(1,-1)]";
        skia composes sequential ops the same way, so we issue them in order.
        Y is negated (pos.y, rotation, skew) to match the SVG renderer's Y-up
        convention.
        """
        if state.pos is not None and (state.pos.x != 0 or state.pos.y != 0):
            canvas.translate(state.pos.x, -state.pos.y)
        if state.rotation:
            canvas.rotate(-state.rotation)
        if state.scale not in (1, 1.0, None):
            canvas.scale(state.scale, state.scale)
        if state.skew_x:
            canvas.skew(math.tan(math.radians(-state.skew_x)), 0.0)
        if state.skew_y:
            canvas.skew(0.0, math.tan(math.radians(-state.skew_y)))
        if getattr(state, "y_up", False):
            canvas.scale(1.0, -1.0)

    @abstractmethod
    def draw_core(self, canvas: skia.Canvas, state: "State", ctx: SkiaContext) -> None:
        """Draw the geometry in local coordinates (no transform/opacity)."""

    # ---- fill/stroke helpers (mirror Renderer._set_fill_and_stroke_kwargs) ----

    @staticmethod
    def fill_paint(state: "State") -> skia.Paint | None:
        """Build a solid-color fill Paint, or None when there is no fill.

        (Gradient/pattern fills are a separate capability, validated up front.)
        """
        color = getattr(state, "fill_color", None)
        if color is None or color.is_none():
            return None
        opacity = getattr(state, "fill_opacity", 1.0)
        paint = skia.Paint(AntiAlias=True, Style=skia.Paint.kFill_Style)
        paint.setColor(skia_color(color, opacity))
        return paint

    @staticmethod
    def stroke_paint(state: "State") -> skia.Paint | None:
        """Build a solid-color stroke Paint, or None when there is no stroke."""
        color = getattr(state, "stroke_color", None)
        width = getattr(state, "stroke_width", 0)
        if color is None or color.is_none() or width <= 0:
            return None
        opacity = getattr(state, "stroke_opacity", 1.0)
        paint = skia.Paint(
            AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=float(width)
        )
        paint.setColor(skia_color(color, opacity))
        return paint
