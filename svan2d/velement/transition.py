"""Transition configuration for keystate segments.

Defines how interpolation happens between two keystates, including:
- Per-field easing functions (speed control)
- Per-field curve functions (spatial trajectory for Point2D fields)
- Morphing configuration (vertex alignment strategies)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple, TypeVar, Union

from svan2d.velement.morphing import MorphingConfig

if TYPE_CHECKING:
    from svan2d.core.point2d import Point2D

# Interpolation function types
CurveFunction = Callable[["Point2D", "Point2D", float], "Point2D"]  # For Point2D fields
RotationFunction = Callable[[float, float, float], float]  # For rotation field
InterpolationFunction = Union[CurveFunction, RotationFunction]  # Generic

# Per-field interpolation configuration: {field_name: interpolation_function}
InterpolationConfig = Dict[str, InterpolationFunction]

# Easing function can return float (1D) or Tuple[float, float] (2D for Point2D)
# EasingFunction = Callable[[float], Union[float, Tuple[float, float]]]


T = TypeVar("T")

EasingFunction = Callable[[float], T]


@dataclass
class TransitionConfig:
    """Transition configuration for segment between keystates.

    Attributes:
        easing_dict: Per-field easing functions {field_name: easing_func}
        morphing_config: Morphing configuration for vertex states
        interpolation_dict: Per-field interpolation functions {field_name: interpolation_func}
                           - Point2D fields: (p1, p2, t) -> Point2D (spatial curves)
                           - Rotation field: (r1, r2, t) -> float (custom rotation)
        linear_angle_interpolation: If True, rotation interpolates linearly without angle wrapping
                         (enables multi-revolution rotation like 0° → 7200°)
        state_interpolation: Optional callable (start_state, end_state, t) -> State that
                            bypasses all per-field interpolation. t is raw segment t (0→1).
    """

    easing_dict: Optional[Dict[str, EasingFunction]] = None
    morphing_config: Optional[Union[MorphingConfig, Dict[str, Any]]] = None
    interpolation_dict: Optional[InterpolationConfig] = None
    linear_angle_interpolation: bool = False
    state_interpolation: Optional[Callable] = None

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(\n"
            f"\teasing={self.easing_dict}, \n"
            f"\tmorphing={self.morphing_config}, \n"
            f"\tinterpolation={self.interpolation_dict}, \n"
            f"\tlinear_angle_interpolation={self.linear_angle_interpolation}, \n"
            f"\tstate_interpolation={self.state_interpolation}\n"
            f")"
        )
