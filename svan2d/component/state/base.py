"""Base State class for all shape states.

States are immutable dataclasses that define geometry, position, and visual attributes.
"""

from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field, replace
from typing import Any, Optional, List

from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.core.color import Color
from svan2d.component.registry import get_renderer_class_for_state
from svan2d.component.effect.filter import Filter


@dataclass(frozen=True)
class State(ABC):
    """Abstract base class for all state classes

    Contains common visual attributes that all renderers can use.
    Subclasses add renderer-specific attributes.

    Default values for center scale, opacity, and rotation are read from
    the configuration system if not explicitly provided.
    """

    pos: Optional[Point2D] = None
    scale: Optional[float] = None
    opacity: Optional[float] = None
    rotation: Optional[float] = None
    skew_x: Optional[float] = None
    skew_y: Optional[float] = None

    # Clipping and masking support
    clip_state: Optional[State] = None
    mask_state: Optional[State] = None
    clip_states: Optional[List[State]] = None
    mask_states: Optional[List[State]] = None

    # Filter support
    filter: Optional[Filter] = None

    # Attributes that should not be interpolated (structural/configuration attributes)
    NON_INTERPOLATABLE_FIELDS: frozenset[str] = frozenset(
        ["NON_INTERPOLATABLE_FIELDS", "DEFAULT_EASING"]
    )

    DEFAULT_EASING = {
        "pos": easing.in_out,
        "scale": easing.in_out,
        "opacity": easing.linear,
        "rotation": easing.in_out,
        "skew_x": easing.linear,
        "skew_y": easing.linear,
        "clip_state": easing.linear,
        "mask_state": easing.linear,
        "clip_states": easing.linear,
        "mask_states": easing.linear,
    }

    # can be overridden by subclasses to add further angle attributes
    # used in interpolation (shortest angle distance)

    def __post_init__(self):
        """Apply configuration defaults for common attributes if not explicitly set"""
        from svan2d.config import get_config, ConfigKey

        config = get_config()

        # Apply config defaults for common attributes if they are None
        if self.pos is None:
            self._set_field("pos", Point2D(0, 0))

        if self.scale is None:
            self._set_field("scale", config.get(ConfigKey.STATE_SCALE, 1.0))
        if self.opacity is None:
            self._set_field("opacity", config.get(ConfigKey.STATE_OPACITY, 1.0))
        if self.rotation is None:
            self._set_field("rotation", config.get(ConfigKey.STATE_ROTATION, 0.0))
        if self.skew_x is None:
            self._set_field("skew_x", config.get(ConfigKey.STATE_SKEW_X, 0.0))
        if self.skew_y is None:
            self._set_field("skew_y", config.get(ConfigKey.STATE_SKEW_Y, 0.0))

    @property
    def x(self) -> float:
        return self.pos.x

    @property
    def y(self) -> float:
        return self.pos.y

    def with_x(self, x: float) -> State:
        return replace(self, pos=self.pos.with_x(x))

    def with_y(self, y: float) -> State:
        return replace(self, pos=self.pos.with_y(y))

    def get_renderer_class(self):
        """Get the renderer class for this state.

        Returns the renderer registered via the @renderer decorator.
        Subclasses can override this method to provide custom renderers.

        Returns:
            The renderer class for this state, or None if not registered

        Note:
            This method should return None to use the registry,
            or return a specific renderer class to override.
        """
        # Base implementation returns None to signal "use the registry"
        # Subclasses can override to return a specific renderer class
        return None

    def get_vertex_renderer_class(self):
        """Get the vertex renderer class for morphing transitions.

        By default, returns the same as get_renderer_class().
        VertexState subclass overrides this to return VertexRenderer.
        """
        return self.get_renderer_class()

    def need_morph(self, state):
        return type(state) is not type(self)

    def is_angle(self, field: field):
        return field.name == "rotation"

    def _none_color(self, field_name: str):
        color = getattr(self, field_name)
        if color is None:
            self._set_field(field_name, Color.NONE)

    def _normalize_color_field(self, field_name: str) -> None:
        """Normalize and set a color field in frozen dataclass

        Args:
            field_name: Name of the field to set

        """
        color = getattr(self, field_name)
        if color is None:
            normalized = Color.NONE
        elif isinstance(color, Color):
            normalized = color
        else:
            normalized = Color(color)

        object.__setattr__(self, field_name, normalized)

    def _set_field(self, name: str, value: Any) -> None:
        """Helper to set attributes in frozen dataclass during __post_init__"""
        object.__setattr__(self, name, value)


States = list[State]
