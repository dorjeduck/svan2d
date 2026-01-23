"""Base State class for all shape states.

States are immutable dataclasses that define geometry, position, and visual attributes.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import Field, dataclass, replace
from typing import Any, List

from svan2d.component.effect.filter import Filter
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D


@dataclass(frozen=True)
class State(ABC):
    """Abstract base class for all state classes

    Contains common visual attributes that all renderers can use.
    Subclasses add renderer-specific attributes.

    Default values for center scale, opacity, and rotation are read from
    the configuration system if not explicitly provided.
    """

    pos: Point2D | None = None
    scale: float | None = None
    opacity: float | None = None
    rotation: float | None = None
    skew_x: float | None = None
    skew_y: float | None = None
    z_index: float = 0.0

    # Clipping and masking support
    clip_state: State | None = None
    mask_state: State | None = None
    clip_states: List[State] | None = None
    mask_states: List[State] | None = None

    # Filter support
    filter: Filter | None = None

    # Attributes that should not be interpolated (structural/configuration attributes)
    NON_INTERPOLATABLE_FIELDS: frozenset[str] = frozenset(["NON_INTERPOLATABLE_FIELDS"])

    # can be overridden by subclasses to add further angle attributes
    # used in interpolation (shortest angle distance)

    def __post_init__(self):
        """Apply configuration defaults for common attributes if not explicitly set"""
        from svan2d.config import ConfigKey, get_config

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
        assert self.pos is not None
        return self.pos.x

    @property
    def y(self) -> float:
        assert self.pos is not None
        return self.pos.y

    def with_x(self, x: float) -> State:
        assert self.pos is not None
        return replace(self, pos=self.pos.with_x(x))

    def with_y(self, y: float) -> State:
        assert self.pos is not None
        return replace(self, pos=self.pos.with_y(y))

    def get_renderer_class(self) -> type | None:
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

    def is_angle(self, field: Field) -> bool:
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
