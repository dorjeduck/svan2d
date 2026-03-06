"""Base element class - minimal abstract interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING

import drawsvg as dw


class _Unset(Enum):
    """Sentinel for distinguishing 'not provided' from ``None``."""
    UNSET = auto()


_UNSET = _Unset.UNSET

if TYPE_CHECKING:
    from svan2d.component.state.base import State


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
    def render(self) -> dw.DrawingElement | None:
        """Render the element in its initial state (static rendering)."""
        pass

    @abstractmethod
    def render_at_frame_time(
        self, t: float, drawing: dw.Drawing | None = None
    ) -> dw.DrawingElement | None:
        """Render the element at a specific animation time."""
        pass

    @abstractmethod
    def is_animatable(self) -> bool:
        """Check if this element can be animated."""
        pass

    @abstractmethod
    def get_frame(self, t: float) -> "State | None":
        """Get the interpolated state at a specific time."""
        pass
