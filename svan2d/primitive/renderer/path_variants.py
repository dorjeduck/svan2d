"""Abstract base class for renderers with multiple path variants"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

import drawsvg as dw

from .base import Renderer

if TYPE_CHECKING:
    from ..state.path_variants import PathVariantsState


class PathVariantsRenderer(Renderer, ABC):
    """Abstract base class for renderers with multiple path variants

    Subclasses just need to define PATH_VARIANTS dictionary with:
    - "variant_name": {
        "path": "SVG path data",
        "viewbox": original_size,
        "center": (cx, cy)
      }
    """

    # Subclasses must define this
    PATH_VARIANTS: dict[str, dict[str, Any]] = {}

    @classmethod
    def variant_data(cls, state: "PathVariantsState") -> dict[str, Any]:
        """The entry of PATH_VARIANTS the state asks for.

        The variant lives on the state, not the renderer, so one renderer
        instance serves every variant and the registry can resolve it from the
        state like any other.
        """
        if not cls.PATH_VARIANTS:
            raise NotImplementedError("Subclass must define PATH_VARIANTS dictionary")

        variant = state.variant
        if variant is None:
            return next(iter(cls.PATH_VARIANTS.values()))
        if variant not in cls.PATH_VARIANTS:
            available = list(cls.PATH_VARIANTS)
            raise ValueError(f"Unknown variant '{variant}'. Available: {available}")
        return cls.PATH_VARIANTS[variant]

    def _render_core(
        self, state: "PathVariantsState", drawing: dw.Drawing | None = None
    ) -> dw.Group:
        """Render the renderer geometry centered at (0,0), no scaling or transforms"""
        variant_data = self.variant_data(state)
        data = variant_data["path"]
        cx, cy = variant_data["center"]

        group = dw.Group(transform=f"translate({-cx},{-cy})")

        paths = data if isinstance(data, list) else [data]
        for path_string in paths:
            path_kwargs = {"d": path_string}
            self._set_fill_and_stroke_kwargs(state, path_kwargs, drawing)
            group.append(dw.Path(**path_kwargs))

        return group

    @classmethod
    def get_available_variants(cls) -> list[str]:
        """Get list of available variants for this renderer"""
        return list(cls.PATH_VARIANTS.keys())
