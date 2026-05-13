"""Renderer for ShapeCollectionState - renders multiple shapes as independent elements"""

from __future__ import annotations

from typing import TYPE_CHECKING

import drawsvg as dw

from svan2d.primitive.renderer.base import Renderer

if TYPE_CHECKING:
    from ..state.state_collection import StateCollectionState


class StateCollectionRenderer(Renderer):
    """Renders a collection of shapes as independent visible elements

    Each shape in the collection is rendered using its own renderer
    and added to a group. Supports M→N morphing automatically via
    the interpolation engine.
    """

    def _render_core(
        self, state: "StateCollectionState", drawing: dw.Drawing | None = None
    ) -> dw.Group:
        """Render each shape in the collection

        Args:
            state: ShapeCollectionState with shapes list
            drawing: Drawing context for definitions

        Returns:
            Group containing all rendered shapes
        """
        group = dw.Group()

        if state.states:
            from svan2d.primitive import get_renderer_instance_for_state

            for s in state.states:
                renderer = get_renderer_instance_for_state(s)
                group.append(renderer.render(s, drawing))

        return group
