"""SVG path morphing with automatic method selection."""

from svan2d.component.state.base import State
from svan2d.component.state.path import MorphMethod
from svan2d.path import SVGPath
from svan2d.transition.morpher import FlubberMorpher, NativeMorpher


class PathMorpher:
    """Handles SVG path interpolation with automatic morph method selection."""

    def interpolate(
        self,
        state: State,
        start_path: SVGPath,
        end_path: SVGPath,
        eased_t: float,
    ) -> SVGPath:
        """
        Interpolate between two SVG paths using appropriate morphing method.

        Morph method priority:
        1. Explicit morph_method on state
        2. Auto-detect: closed paths use shape morph, open paths use stroke morph

        Args:
            state: State containing optional morph_method
            start_path: Starting SVG path
            end_path: Ending SVG path
            eased_t: Eased interpolation parameter

        Returns:
            Interpolated SVG path
        """
        morph_method = getattr(state, "morph_method", None)

        # Explicit shape morph
        if morph_method == MorphMethod.SHAPE or morph_method == "shape":
            return FlubberMorpher.for_paths(start_path, end_path)(eased_t)

        # Explicit stroke morph
        if morph_method == MorphMethod.STROKE or morph_method == "stroke":
            return NativeMorpher.for_paths(start_path, end_path)(eased_t)

        # Auto-detect: use shape morph for closed paths, stroke for open
        if self._is_closed(start_path):
            return FlubberMorpher.for_paths(start_path, end_path)(eased_t)
        else:
            return NativeMorpher.for_paths(start_path, end_path)(eased_t)

    def _is_closed(self, path: SVGPath, tolerance: float = 0.01) -> bool:
        """
        Check if an SVG path is closed.

        A path is considered closed if:
        1. It ends with a 'Z' command, or
        2. The start and end points are within tolerance distance

        Args:
            path: SVG path to check
            tolerance: Maximum distance between start/end points to consider closed

        Returns:
            True if path is closed
        """
        # Check for explicit 'Z' close command
        path_str = path.to_string().strip().upper()
        if path_str.endswith("Z"):
            return True

        # Check if start and end points are close enough
        if len(path.commands) < 2:
            return False

        start_cmd = path.commands[0]
        end_cmd = path.commands[-1]

        if not (hasattr(start_cmd, "x") and hasattr(end_cmd, "x")):
            return False

        distance = (
            (getattr(end_cmd, "x") - getattr(start_cmd, "x")) ** 2 +
            (getattr(end_cmd, "y") - getattr(start_cmd, "y")) ** 2
        ) ** 0.5

        return distance <= tolerance
