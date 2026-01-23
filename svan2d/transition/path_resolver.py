"""Path function resolution with 2-level priority system"""

from typing import TYPE_CHECKING, Callable, Dict, Optional

if TYPE_CHECKING:
    from svan2d.core.point2d import Point2D

# Path function type
PathFunction = Callable[["Point2D", "Point2D", float], "Point2D"]

# Per-field path configuration
PathConfig = Dict[str, PathFunction]


class PathResolver:
    """
    Resolves path functions for Point2D animations using a 2-level priority system.

    Priority (highest to lowest):
    1. Segment-level path (from KeyState.transition.path dict)
    2. Global default (linear)

    Path functions can apply to any Point2D field, specified by field name.
    """

    def __init__(self):
        """Initialize the path resolver."""
        pass

    def get_path_for_field(
        self,
        field_name: str,
        segment_path_config: Optional[PathConfig] = None,
    ) -> PathFunction:
        """
        Get the path function for a specific field following the 2-level priority.

        Args:
            field_name: Name of the Point2D field (e.g., "pos", "anchor")
            segment_path_config: Optional segment-level path config dict
                                 {field_name: path_function}

        Returns:
            Path function to apply for Point2D interpolation of this field
        """
        # Level 1: Segment-level path for this field (highest priority)
        if segment_path_config is not None and field_name in segment_path_config:
            return segment_path_config[field_name]

        # Level 2: Global default (linear)
        from svan2d.transition.curve import linear
        return linear

    def get_path(
        self,
        segment_path: Optional[PathFunction] = None,
    ) -> PathFunction:
        """
        Get the path function following the 2-level priority.

        DEPRECATED: Use get_path_for_field() instead for per-field path support.

        Args:
            segment_path: Optional segment-level path function

        Returns:
            Path function to apply for Point2D interpolation
        """
        # Level 1: Segment-level path (highest priority)
        if segment_path is not None:
            return segment_path

        # Level 2: Global default (linear)
        from svan2d.transition.curve import linear
        return linear
