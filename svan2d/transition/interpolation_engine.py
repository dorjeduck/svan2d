"""State and value interpolation engine"""

import logging
from dataclasses import fields, replace
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from svan2d.component.effect.filter.base import Filter
from svan2d.component.effect.gradient.base import Gradient
from svan2d.component.effect.pattern.base import Pattern
from svan2d.component.state.base import State
from svan2d.component.vertex.vertex_contours import VertexContours
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.core.scalar_functions import lerp
from svan2d.path import SVGPath
from svan2d.transition.interpolators import (
    StateInterpolator,
    VertexContoursInterpolator,
)
from svan2d.transition.path_morpher import PathMorpher
from svan2d.transition.state_list_interpolator import (
    StateListInterpolator,
    _normalize_to_state_list,
)
from svan2d.transition.type_interpolators import TypeInterpolators

logger = logging.getLogger(__name__)


# Type alias for easing result - can be scalar (normal) or tuple (2D easing)
EasedT = Union[float, Tuple[float, float]]


def _scalar_t(eased_t: EasedT) -> float:
    """Extract scalar t value from EasedT.

    For 2D easing (tuple), uses the first component.
    For scalar easing, returns the value directly.
    """
    if isinstance(eased_t, tuple):
        return eased_t[0]
    return eased_t


class InterpolationEngine:
    """Handles interpolation of states and individual values."""

    def __init__(self, easing_resolver, path_resolver=None):
        """
        Initialize the interpolation engine.

        Args:
            easing_resolver: EasingResolver instance for determining easing functions
            path_resolver: PathResolver instance for determining path functions (optional)
        """
        self.easing_resolver = easing_resolver
        self.path_resolver = path_resolver

        # Specialized interpolators
        self._shape_list_interpolator = StateListInterpolator(self)
        self._vertex_contours_interpolator = VertexContoursInterpolator()
        self._state_interpolator = StateInterpolator(self)
        self._path_morpher = PathMorpher()
        self._type_interpolators = TypeInterpolators(path_resolver)

    @staticmethod
    def compute_changed_fields(
        start_state: State,
        end_state: State,
        attribute_keystates_fields: set,
    ) -> Tuple[set, Dict[str, Tuple[Any, Any]]]:
        """Pre-compute which fields differ between two states.

        Returns:
            Tuple of (set of changed field names, dict of field_name -> (start_val, end_val))
        """
        changed = set()
        field_values = {}
        non_interp = start_state.NON_INTERPOLATABLE_FIELDS

        for field in fields(start_state):
            field_name = field.name

            # Skip class-level constants (not real instance fields)
            if field_name == "NON_INTERPOLATABLE_FIELDS":
                continue

            # Skip attributes managed by attribute_keystates
            if field_name in attribute_keystates_fields:
                continue

            # Non-interpolatable fields always need processing (step function)
            if field_name in non_interp:
                start_val = getattr(start_state, field_name)
                end_val = getattr(end_state, field_name, start_val)
                if start_val != end_val:
                    changed.add(field_name)
                    field_values[field_name] = (start_val, end_val)
                continue

            start_val = getattr(start_state, field_name)
            if not hasattr(end_state, field_name):
                continue

            end_val = getattr(end_state, field_name)

            # Only track fields that actually differ
            if start_val != end_val:
                changed.add(field_name)
                field_values[field_name] = (start_val, end_val)

        return changed, field_values

    def create_eased_state(
        self,
        start_state: State,
        end_state: State,
        t: float,
        segment_easing_overrides: Optional[Dict[str, Callable[[float], float]]],
        attribute_keystates_fields: set,
        vertex_buffer: Optional[Tuple[List, List[List]]] = None,
        segment_interpolation_config: Optional[Dict[str, Callable]] = None,
        morphing_config: Optional[Any] = None,
        changed_fields: Optional[Tuple[set, Dict[str, Tuple[Any, Any]]]] = None,
        linear_angle_interpolation: bool = False,
    ) -> State:
        """
        Create an interpolated state between two keystates.

        Args:
            start_state: Starting state
            end_state: Ending state
            t: Interpolation parameter (0.0 to 1.0)
            segment_easing_overrides: Per-segment easing overrides
            attribute_keystates_fields: Attributes managed by field keystates
            vertex_buffer: Optional reusable buffer for vertex interpolation
            segment_interpolation_config: Optional per-field path config dict {field_name: path_func}
            morphing_config: Optional morphing configuration (Morphing or MorphingConfig)
            changed_fields: Optional pre-computed (changed_field_names, field_values) tuple
            linear_angle_interpolation: If True, rotation uses linear interpolation (no angle wrapping)
        """
        interpolated_values = {}

        # Extract mapper/aligner once (not per-field)
        mapper = None
        vertex_aligner = None
        if morphing_config is not None:
            if hasattr(morphing_config, "mapper"):
                mapper = morphing_config.mapper
                vertex_aligner = morphing_config.vertex_aligner
            elif isinstance(morphing_config, dict):
                mapper = morphing_config.get("mapper")
                vertex_aligner = morphing_config.get("vertex_aligner")

        # Use pre-computed changed fields if available (lazy field interpolation)
        if changed_fields is not None:
            changed_names, field_values = changed_fields

            for field_name in changed_names:
                start_value, end_value = field_values[field_name]

                # Non-interpolatable: step function
                if field_name in start_state.NON_INTERPOLATABLE_FIELDS:
                    interpolated_values[field_name] = (
                        start_value if t < 0.5 else end_value
                    )
                    continue

                # Get easing function for this field
                easing_func = self.easing_resolver.get_easing_for_field(
                    start_state, field_name, segment_easing_overrides
                )
                eased_t = easing_func(t) if easing_func else t

                # Interpolate the value
                interpolated_values[field_name] = self.interpolate_value(
                    start_state,
                    end_state,
                    field_name,
                    start_value,
                    end_value,
                    eased_t,
                    vertex_buffer,
                    segment_interpolation_config,
                    mapper=mapper,
                    vertex_aligner=vertex_aligner,
                    linear_angle_interpolation=linear_angle_interpolation,
                )
        else:
            # Fallback: iterate all fields (original behavior)
            for field in fields(start_state):
                field_name = field.name

                # Skip attributes managed by attribute_keystates
                if field_name in attribute_keystates_fields:
                    continue

                # Skip non-interpolatable attributes (structural/configuration attributes)
                if field_name in start_state.NON_INTERPOLATABLE_FIELDS:
                    start_value = getattr(start_state, field_name)
                    interpolated_values[field_name] = (
                        start_value
                        if t < 0.5
                        else getattr(end_state, field_name, start_value)
                    )
                    continue

                start_value = getattr(start_state, field_name)

                if not hasattr(end_state, field_name):
                    continue

                end_value = getattr(end_state, field_name)

                # No interpolation needed if values are identical AND no custom interpolation function
                if start_value == end_value and (
                    segment_interpolation_config is None
                    or field_name not in segment_interpolation_config
                ):
                    interpolated_values[field_name] = start_value
                    continue

                # Get easing function for this field
                easing_func = self.easing_resolver.get_easing_for_field(
                    start_state, field_name, segment_easing_overrides
                )
                eased_t = easing_func(t) if easing_func else t

                # Interpolate the value
                interpolated_values[field_name] = self.interpolate_value(
                    start_state,
                    end_state,
                    field_name,
                    start_value,
                    end_value,
                    eased_t,
                    vertex_buffer,
                    segment_interpolation_config,
                    mapper=mapper,
                    vertex_aligner=vertex_aligner,
                    linear_angle_interpolation=linear_angle_interpolation,
                )

        if t < 0.5:
            return replace(start_state, **interpolated_values)
        else:
            return replace(end_state, **interpolated_values)

    def interpolate_value(
        self,
        start_state: State,
        end_state: State,
        field_name: str,
        start_value: Any,
        end_value: Any,
        eased_t: EasedT,
        vertex_buffer: Optional[Tuple[List, List[List]]] = None,
        segment_interpolation_config: Optional[Dict[str, Callable]] = None,
        mapper: Optional[Any] = None,
        vertex_aligner: Optional[Any] = None,
        linear_angle_interpolation: bool = False,
    ) -> Any:
        """
        Interpolate a single value based on its type and context.

        Dispatches to specialized interpolators based on value type.

        Args:
            start_state: Start state object for context
            end_state: End state object
            field_name: Name of the field being interpolated
            start_value: Starting value
            end_value: Ending value
            eased_t: Eased interpolation parameter (0.0 to 1.0)
            vertex_buffer: Optional reusable buffer for vertex interpolation
            segment_interpolation_config: Optional per-field path config dict
            mapper: Optional mapper for M→N matching
            vertex_aligner: Optional vertex aligner for shape morphing
            linear_angle_interpolation: If True, rotation uses linear interpolation (no angle wrapping)

        Returns:
            Interpolated value
        """
        # Convert to scalar t for methods that don't support 2D easing
        scalar_t = _scalar_t(eased_t)

        # List[State] interpolation (clip_states, mask_states, etc.)
        is_list_field = isinstance(start_value, list) or isinstance(end_value, list)
        if is_list_field:
            start_list = _normalize_to_state_list(start_value)
            end_list = _normalize_to_state_list(end_value)
            if start_list is not None and end_list is not None:
                return self._shape_list_interpolator.interpolate_state_list(
                    start_list,
                    end_list,
                    scalar_t,
                    mapper=mapper,
                    vertex_aligner=vertex_aligner,
                )

        # VertexContours interpolation (aligned vertices for morphing)
        if (
            field_name == "_aligned_contours"
            and isinstance(start_value, VertexContours)
            and isinstance(end_value, VertexContours)
        ):
            return self._vertex_contours_interpolator.interpolate(
                start_state,
                end_state,
                start_value,
                end_value,
                scalar_t,
                vertex_buffer,
            )

        # State interpolation (for clip_state, mask_state, and recursive calls)
        if isinstance(start_value, State) and isinstance(end_value, State):
            return self._state_interpolator.interpolate(
                start_value,
                end_value,
                scalar_t,
                mapper=mapper,
                vertex_aligner=vertex_aligner,
            )

        # Effect interpolation (Gradient, Pattern, Filter)
        if isinstance(start_value, Gradient) and isinstance(end_value, Gradient):
            return start_value.interpolate(end_value, scalar_t)  # type: ignore[union-attr]
        if isinstance(start_value, Pattern) and isinstance(end_value, Pattern):
            return start_value.interpolate(end_value, scalar_t)  # type: ignore[union-attr]
        if isinstance(start_value, Filter) and isinstance(end_value, Filter):
            return start_value.interpolate(end_value, scalar_t)  # type: ignore[union-attr]
        if isinstance(start_value, (Gradient, Pattern, Filter)):
            return start_value  # Can't interpolate between different effect types

        # State ↔ None transitions (fade in/out)
        if isinstance(start_value, State) and end_value is None:
            assert isinstance(start_value, State)  # Help type checker
            start_opacity = (
                start_value.opacity if start_value.opacity is not None else 1.0
            )
            return replace(start_value, opacity=lerp(start_opacity, 0.0, scalar_t))
        if start_value is None and isinstance(end_value, State):
            assert isinstance(end_value, State)  # Help type checker
            end_opacity = end_value.opacity if end_value.opacity is not None else 1.0
            return replace(end_value, opacity=lerp(0.0, end_opacity, scalar_t))

        # Point2D interpolation (can use full eased_t for 2D easing)
        if isinstance(start_value, Point2D) and isinstance(end_value, Point2D):
            return self._type_interpolators.interpolate_point2d(
                start_value,
                end_value,
                eased_t,
                field_name,
                segment_interpolation_config,
            )

        # SVG Path interpolation
        if isinstance(start_value, SVGPath) and isinstance(end_value, SVGPath):
            return self._path_morpher.interpolate(
                start_state, start_value, end_value, scalar_t
            )

        # Color interpolation
        if isinstance(start_value, Color) and isinstance(end_value, Color):
            return self._type_interpolators.interpolate_color(
                start_value, end_value, eased_t
            )

        # Rotation interpolation function (custom rotation logic) - check BEFORE angle interpolation
        if (
            segment_interpolation_config is not None
            and field_name in segment_interpolation_config
            and self._type_interpolators.is_angle_field(start_state, field_name)
            and isinstance(start_value, (int, float))
            and isinstance(end_value, (int, float))
        ):
            rotation_func = segment_interpolation_config[field_name]
            scalar_t = self._type_interpolators._extract_scalar_t(eased_t)
            return rotation_func(start_value, end_value, scalar_t)

        # Angle interpolation (handles wraparound unless linear_angle_interpolation is True)
        if (
            self._type_interpolators.is_angle_field(start_state, field_name)
            and isinstance(start_value, (int, float))
            and isinstance(end_value, (int, float))
            and not linear_angle_interpolation
        ):
            return self._type_interpolators.interpolate_angle(
                start_value, end_value, eased_t
            )

        # Numeric interpolation
        if isinstance(start_value, (int, float)) and isinstance(
            end_value, (int, float)
        ):
            return self._type_interpolators.interpolate_numeric(
                start_value, end_value, eased_t
            )

        # Non-numeric values: step function at t=0.5
        return self._type_interpolators.interpolate_step(
            start_value, end_value, eased_t
        )
