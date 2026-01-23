"""Abstract base class for renderers with multiple path variants"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, Dict, Optional

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
    PATH_VARIANTS: Dict[str, Dict[str, Any]] = {}

    def __init__(self, variant: Optional[str] = None) -> None:
        """Initialize multi-path renderer

        Args:
            variant: Path variant name. If None, uses first available variant
        """
        if not self.PATH_VARIANTS:
            raise NotImplementedError("Subclass must define PATH_VARIANTS dictionary")

        # Use first variant as default if none specified
        if variant is None:
            variant = list(self.PATH_VARIANTS.keys())[0]

        if variant not in self.PATH_VARIANTS:
            available = list(self.PATH_VARIANTS.keys())
            raise ValueError(f"Unknown variant '{variant}'. Available: {available}")

        self.variant = variant
        self.data = self.PATH_VARIANTS[variant]

    def _render_core(
        self, state: "PathVariantsState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Group:
        """Render the renderer geometry centered at (0,0), no scaling or transforms"""
        fill_color = state.fill_color.to_rgb_string()
        data = self.data["path"]

        cx, cy = self.data["center"]

        viewbox_size = self.data["viewbox"]
        scale_factor = state.size / viewbox_size
        group = dw.Group(transform=f"scale({scale_factor}) translate({-cx},{-cy})")

        paths = data if isinstance(data, list) else [data]
        for path_string in paths:
            path_kwargs = {"d": path_string}
            self._set_fill_and_stroke_kwargs(state, path_kwargs, drawing)

            group.append(dw.Path(**path_kwargs))
        group.transform = f"translate({-cx},{-cy})"  # type: ignore[attr-defined]
        return group

    @classmethod
    def get_available_variants(cls) -> list[str]:
        """Get list of available variants for this renderer"""
        return list(cls.PATH_VARIANTS.keys())

    def get_current_variant(self) -> str:
        """Get the currently selected variant"""
        return self.variant

    def set_variant(self, variant: str) -> None:
        """Set the current variant

        Args:
            variant: Path variant name to set

        Raises:
            ValueError: If variant is not available
        """
        if variant not in self.PATH_VARIANTS:
            available = list(self.PATH_VARIANTS.keys())
            raise ValueError(f"Unknown variant '{variant}'. Available: {available}")

        self.variant = variant
        self.data = self.PATH_VARIANTS[variant]
