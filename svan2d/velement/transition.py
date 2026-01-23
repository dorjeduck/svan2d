"""Transition configuration for keystate segments.

Defines how interpolation happens between two keystates, including:
- Per-field easing functions (speed control)
- Per-field curve functions (spatial trajectory for Point2D fields)
- Morphing configuration (vertex alignment strategies)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Union

from svan2d.velement.morphing import MorphingConfig

if TYPE_CHECKING:
    from svan2d.core.point2d import Point2D

# Curve function type: (start_point, end_point, t) -> interpolated_point
CurveFunction = Callable[["Point2D", "Point2D", float], "Point2D"]

# Per-field curve configuration: {field_name: curve_function}
CurveConfig = Dict[str, CurveFunction]


@dataclass
class TransitionConfig:
    """Transition configuration for segment between keystates.

    Attributes:
        easing_dict: Per-field easing functions {field_name: easing_func}
        morphing_config: Morphing configuration for vertex states
        curve_dict: Per-field curve functions {field_name: curve_func}
                    Curve functions control spatial trajectory for Point2D interpolation.
    """

    easing_dict: Optional[Dict[str, Callable[[float], float]]] = None
    morphing_config: Optional[Union[MorphingConfig, Dict[str, Any]]] = None
    curve_dict: Optional[CurveConfig] = None

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(\n"
            f"\teasing={self.easing_dict}, \n"
            f"\tmorphing={self.morphing_config}, \n"
            f"\tcurves={self.curve_dict}\n"
            f")"
        )
