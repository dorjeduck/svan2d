from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Union, TYPE_CHECKING

from svan2d.velement.morphing import Morphing

if TYPE_CHECKING:
    from svan2d.core.point2d import Point2D

# Path function type: (start_point, end_point, t) -> interpolated_point
PathFunction = Callable[["Point2D", "Point2D", float], "Point2D"]

# Per-field path configuration: {field_name: path_function}
PathConfig = Dict[str, PathFunction]


@dataclass
class TransitionConfig:
    """Transition configuration for segment between keystates

    Attributes:
        easing: Per-field easing functions {field_name: easing_func}
        morphing: Morphing configuration for vertex states
        path: Per-field path functions {field_name: path_func}
              Path functions control spatial trajectory for Point2D interpolation.
    """
    easing: Optional[Dict[str, Callable[[float], float]]] = None
    morphing: Optional[Union[Morphing, Dict[str, Any]]] = None
    path: Optional[PathConfig] = None
