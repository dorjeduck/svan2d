"""Skia renderer for StateCollectionState — mirror of StateCollectionRenderer.

Draws each child state with its own Skia renderer onto the same canvas. The
collection's own transform/opacity is applied by SkiaRenderer.draw before
draw_core runs; each child's draw() then applies its own transform on top.
"""

from __future__ import annotations

from svan2d.primitive.state.state_collection import StateCollectionState
from svan2d.skia.base import SkiaContext, SkiaRenderer


class StateCollectionSkiaRenderer(SkiaRenderer):
    """Renders each state in the collection as an independent element."""

    def draw_core(self, canvas, state: StateCollectionState, ctx: SkiaContext) -> None:
        if not state.states:
            return
        from svan2d.primitive.registry import get_skia_renderer_for_state

        for s in state.states:
            get_skia_renderer_for_state(s).draw(canvas, s, ctx)
