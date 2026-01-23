"""Renderer for ShapeCollectionState - renders multiple shapes as independent elements"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import drawsvg as dw

from svan2d.component.renderer.base import Renderer

if TYPE_CHECKING:
    from ..state.state_collection import StateCollectionState


class StateCollectionRenderer(Renderer):
    """Renders a collection of shapes as independent visible elements

    Each shape in the collection is rendered using its own renderer
    and added to a group. Supports M→N morphing automatically via
    the interpolation engine.
    """

    def _render_core(
        self, state: "StateCollectionState", drawing: Optional[dw.Drawing] = None
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
            # Import here to avoid circular dependency
            from svan2d.component import get_renderer_instance_for_state
            from svan2d.component.renderer.base_vertex import VertexRenderer

            for s in state.states:
                # Check if this is a morph state (has _aligned_contours from interpolation)
                if (
                    hasattr(s, "_aligned_contours")
                    and s._aligned_contours is not None
                ):
                    # This is an interpolated state between different shape types
                    # Use VertexRenderer for smooth morphing
                    renderer = VertexRenderer()
                else:
                    # Normal state - use its registered renderer
                    renderer = get_renderer_instance_for_state(s)

                # Render the shape (applies transforms, opacity, clips, etc.)
                rendered = renderer.render(s, drawing)

                # Add to collection group
                group.append(rendered)

        return group
