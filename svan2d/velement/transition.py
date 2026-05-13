"""Transition configuration for keystate segments.

Defines how interpolation happens between two keystates, including:
- Per-field easing functions (speed control)
- Per-field curve functions (spatial trajectory for Point2D fields)
- Morphing configuration (vertex alignment strategies)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from svan2d.velement.morphing import MorphingConfig

if TYPE_CHECKING:
    from svan2d.core.point2d import Point2D

# Interpolation function types
CurveFunction = Callable[["Point2D", "Point2D", float], "Point2D"]  # For Point2D fields
RotationFunction = Callable[[float, float, float], float]  # For rotation field
InterpolationFunction = CurveFunction | RotationFunction  # Generic

# Per-field interpolation configuration: {field_name: interpolation_function}
InterpolationConfig = dict[str, InterpolationFunction]

T = TypeVar("T")

EasingFunction = Callable[[float], T]


@dataclass
class TransitionConfig:
    """Transition configuration for segment between keystates.

    Attributes:
        easing: Blanket easing function applied to all fields. Overridden by
                easing_dict entries for specific fields.
        easing_dict: Per-field easing functions {field_name: easing_func}
        morphing_config: Morphing configuration for vertex states
        interpolation_dict: Per-field interpolation functions {field_name: interpolation_func}
                           - Point2D fields: (p1, p2, t) -> Point2D (spatial curves)
                           - Rotation field: (r1, r2, t) -> float (custom rotation)
        exact_rotation: If True, rotation uses the exact angle value — no shortest-arc
                         optimization. Use to force a direction (e.g. always clockwise)
                         or for multi-revolution rotation (e.g. 0° → 720°).
        state_interpolation: Optional callable (start_state, end_state, t) -> State that
                            bypasses all per-field interpolation. t is raw segment t (0→1).
        covers_boundaries: If True and state_interpolation is set, the state_interpolation
                          function is called even at exact boundary t values (segment start/end)
                          instead of returning the keystate directly.
    """

    easing: EasingFunction | None = None
    easing_dict: dict[str, EasingFunction] | None = None
    morphing_config: MorphingConfig | dict[str, Any] | None = None
    interpolation_dict: InterpolationConfig | None = None
    exact_rotation: bool = False
    state_interpolation: Callable | None = None
    covers_boundaries: bool = False

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(\n"
            f"\teasing={self.easing}, \n"
            f"\teasing_dict={self.easing_dict}, \n"
            f"\tmorphing={self.morphing_config}, \n"
            f"\tinterpolation={self.interpolation_dict}, \n"
            f"\texact_rotation={self.exact_rotation}, \n"
            f"\tstate_interpolation={self.state_interpolation}, \n"
            f"\tcovers_boundaries={self.covers_boundaries}\n"
            f")"
        )
