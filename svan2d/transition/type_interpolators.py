"""Type-specific interpolation handlers for primitive and common types."""

from dataclasses import fields
from typing import Any, Callable, Dict, Optional, Tuple, Union

from svan2d.component.state.base import State
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.core.scalar_functions import angle, lerp, step

# Type alias for easing result - can be scalar (normal) or tuple (2D easing)
EasedT = Union[float, Tuple[float, float]]


class TypeInterpolators:
    """Handles interpolation of primitive and common value types."""

    @staticmethod
    def _extract_scalar_t(eased_t: EasedT) -> float:
        """Convert 2D easing tuple to scalar by averaging."""
        if isinstance(eased_t, (int, float)):
            return eased_t
        return (eased_t[0] + eased_t[1]) / 2

    def __init__(self, path_resolver=None):
        """
        Initialize type interpolators.

        Args:
            path_resolver: PathResolver instance for Point2D path functions (optional)
        """
        self.path_resolver = path_resolver

    def interpolate_point2d(
        self,
        start_value: Point2D,
        end_value: Point2D,
        eased_t: EasedT,
        field_name: str,
        segment_path_config: Optional[Dict[str, Callable]] = None,
    ) -> Point2D:
        """
        Interpolate between two Point2D values.

        Supports:
        - Path functions for custom trajectories
        - 2D easing (separate easing for x and y)
        - Standard linear interpolation

        Args:
            start_value: Starting Point2D
            end_value: Ending Point2D
            eased_t: Eased interpolation parameter (scalar or 2D tuple)
            field_name: Name of the field being interpolated
            segment_path_config: Optional per-field path config dict

        Returns:
            Interpolated Point2D
        """
        # Check for path function for this specific field
        if self.path_resolver and segment_path_config is not None:
            path_func = self.path_resolver.get_path_for_field(
                field_name, segment_path_config
            )
            # Only use path if one was configured for this field
            if segment_path_config.get(field_name) is not None:
                scalar_t = self._extract_scalar_t(eased_t)
                return path_func(start_value, end_value, scalar_t)

        # 2D easing (when no explicit path set for this field)
        if isinstance(eased_t, tuple):
            tx, ty = eased_t
            return Point2D(
                lerp(start_value.x, end_value.x, tx),
                lerp(start_value.y, end_value.y, ty),
            )
        else:
            return start_value.lerp(end_value, eased_t)

    def interpolate_color(
        self,
        start_value: Color,
        end_value: Color,
        eased_t: EasedT,
    ) -> Color:
        """
        Interpolate between two Color values.

        Args:
            start_value: Starting Color
            end_value: Ending Color
            eased_t: Eased interpolation parameter

        Returns:
            Interpolated Color
        """
        return start_value.interpolate(end_value, self._extract_scalar_t(eased_t))

    def interpolate_angle(
        self,
        start_value: float,
        end_value: float,
        eased_t: EasedT,
    ) -> float:
        """
        Interpolate between two angle values with wraparound handling.

        Args:
            start_value: Starting angle
            end_value: Ending angle
            eased_t: Eased interpolation parameter

        Returns:
            Interpolated angle
        """
        scalar_t = self._extract_scalar_t(eased_t)
        return angle(start_value, end_value, scalar_t)

    def interpolate_numeric(
        self,
        start_value: Union[int, float],
        end_value: Union[int, float],
        eased_t: EasedT,
    ) -> float:
        """
        Interpolate between two numeric values.

        Args:
            start_value: Starting number
            end_value: Ending number
            eased_t: Eased interpolation parameter

        Returns:
            Interpolated number
        """
        scalar_t = self._extract_scalar_t(eased_t)
        return lerp(start_value, end_value, scalar_t)

    def interpolate_step(
        self,
        start_value: Any,
        end_value: Any,
        eased_t: EasedT,
    ) -> Any:
        """
        Step interpolation for non-numeric values.

        Switches from start to end at t=0.5.

        Args:
            start_value: Starting value
            end_value: Ending value
            eased_t: Eased interpolation parameter

        Returns:
            start_value if t < 0.5, else end_value
        """
        scalar_t = self._extract_scalar_t(eased_t)
        return step(start_value, end_value, scalar_t)

    def is_angle_field(self, state: State, field_name: str) -> bool:
        """
        Check if a field represents an angle value.

        Args:
            state: State object
            field_name: Name of the field to check

        Returns:
            True if field represents an angle
        """
        if not hasattr(state, "is_angle"):
            return False

        field_obj = next((f for f in fields(state) if f.name == field_name), None)
        if field_obj:
            return state.is_angle(field_obj)

        return False
