"""Base element class - minimal abstract interface."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

import drawsvg as dw


class BaseVElement(ABC):
    """Abstract base class for all animatable elements.

    Provides the minimal interface that all VElement types must implement.
    Animation logic has been extracted to:
    - KeystateBuilder: Builder pattern mixin
    - StateInterpolator: State interpolation
    - VertexAligner: Vertex morphing alignment
    - AttributeTimelineResolver: Per-field timelines
    """

    @abstractmethod
    def render(self) -> Optional[dw.DrawingElement]:
        """Render the element in its initial state (static rendering)."""
        pass

    @abstractmethod
    def render_at_frame_time(
        self, t: float, drawing: Optional[dw.Drawing] = None
    ) -> Optional[dw.DrawingElement]:
        """Render the element at a specific animation time."""
        pass

    @abstractmethod
    def is_animatable(self) -> bool:
        """Check if this element can be animated."""
        pass

    @abstractmethod
    def get_frame(self, t: float):
        """Get the interpolated state at a specific time."""
        pass
