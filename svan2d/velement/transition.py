from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Union, TYPE_CHECKING

from svan2d.velement.morphing import Morphing

if TYPE_CHECKING:
    from svan2d.core.point2d import Point2D

# Path function type: (start_point, end_point, t) -> interpolated_point
CurveFunction = Callable[["Point2D", "Point2D", float], "Point2D"]

# Per-field path configuration: {field_name: path_function}
CurveConfig = Dict[str, CurveFunction]


@dataclass
class TransitionConfig:
    """Transition configuration for segment between keystates

    Attributes:
        easing_dict: Per-field easing functions {field_name: easing_func}
        morphing: Morphing configuration for vertex states
        path: Per-field path functions {field_name: path_func}
              Path functions control spatial trajectory for Point2D interpolation.
    """

    easing_dict: Optional[Dict[str, Callable[[float], float]]] = None
    morphing: Optional[Union[Morphing, Dict[str, Any]]] = None
    curve_dict: Optional[CurveConfig] = None
