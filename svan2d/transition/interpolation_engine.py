"""State and value interpolation engine"""

from typing import Any, Callable, Dict, Optional, Tuple, List, Union
from dataclasses import fields, replace
import logging

# Type alias for easing result - can be scalar (normal) or tuple (2D easing)
EasedT = Union[float, Tuple[float, float]]

from svan2d.component.state.base import State
from svan2d.component.effect.gradient.base import Gradient
from svan2d.component.effect.pattern.base import Pattern
from svan2d.component.effect.filter.base import Filter
from svan2d.component.state.path import MorphMethod
from svan2d.component.vertex.vertex_contours import VertexContours
from svan2d.component.vertex.vertex_loop import VertexLoop
from svan2d.core.point2d import Point2D, Points2D
from svan2d.path import SVGPath
from svan2d.transition import lerp, step, angle, inbetween, circular_midpoint
from svan2d.transition.morpher import NativeMorpher, FlubberMorpher
from svan2d.core.color import Color
from svan2d.transition.state_list_interpolator import (
    StateListInterpolator,
    _normalize_to_state_list,
)

logger = logging.getLogger(__name__)


class InterpolationEngine:
    """Handles interpolation of states and individual values"""

    def __init__(self, easing_resolver, path_resolver=None):
        """
        Initialize the interpolation engine.

        Args:
            easing_resolver: EasingResolver instance for determining easing functions
            path_resolver: PathResolver instance for determining path functions (optional)
        """
        self.easing_resolver = easing_resolver
        self.path_resolver = path_resolver
        self._shape_list_interpolator = StateListInterpolator(self)

    def create_eased_state(
        self,
        start_state: State,
        end_state: State,
        t: float,
        segment_easing_overrides: Optional[Dict[str, Callable[[float], float]]],
        attribute_keystates_fields: set,
        vertex_buffer: Optional[Tuple[List, List[List]]] = None,
        segment_path_config: Optional[Dict[str, Callable]] = None,
        morphing_config: Optional[Any] = None,
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
            segment_path_config: Optional per-field path config dict {field_name: path_func}
            morphing_config: Optional morphing configuration (Morphing or MorphingConfig)
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

            # No interpolation needed if values are identical
            if start_value == end_value:
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
                segment_path_config,
                mapper=mapper,
                vertex_aligner=vertex_aligner,
            )

        # return replace(start_state, **interpolated_values)

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
        eased_t: float,
        vertex_buffer: Optional[Tuple[List, List[List]]] = None,
        segment_path_config: Optional[Dict[str, Callable]] = None,
        mapper: Optional[Any] = None,
        vertex_aligner: Optional[Any] = None,
    ) -> Any:
        """
        Interpolate a single value based on its type and context.

        Args:
            start_state: Start state object for context (e.g., morph method for paths)
            end_state: End state object
            field_name: Name of the field being interpolated
            start_value: Starting value
            end_value: Ending value
            eased_t: Eased interpolation parameter (0.0 to 1.0)
            vertex_buffer: Optional reusable buffer for vertex interpolation
                          (outer_buffer, hole_buffers) to avoid allocations
            segment_path_config: Optional per-field path config dict {field_name: path_func}
            mapper: Optional mapper for M→N matching
            vertex_aligner: Optional vertex aligner for shape morphing

        Returns:
            Interpolated value
        """
        # Check for List[State] interpolation (clip_states, mask_states, etc.)
        # IMPORTANT: Only normalize if we have actual lists, not single State objects
        # This prevents infinite recursion when interpolating states within lists
        is_list_field = isinstance(start_value, list) or isinstance(end_value, list)

        if is_list_field:
            start_list = _normalize_to_state_list(start_value)
            end_list = _normalize_to_state_list(end_value)

            if start_list is not None and end_list is not None:
                # Both are state lists (or normalizable to lists)
                return self._shape_list_interpolator.interpolate_state_list(
                    start_list,
                    end_list,
                    eased_t,
                    mapper=mapper,
                    vertex_aligner=vertex_aligner,
                )

        if (
            field_name == "_aligned_contours"
            and isinstance(start_value, VertexContours)
            and isinstance(end_value, VertexContours)
        ):

            # Handle empty contours - use step interpolation at midpoint
            if not start_value or not end_value:
                logger.warning(
                    "One or both contours are empty during interpolation. "
                    "Using step interpolation at t=0.5. This may indicate a "
                    "problem with contour generation."
                )
                return start_value if eased_t < 0.5 else end_value

            if len(start_value.outer) != len(end_value.outer):
                raise ValueError(
                    f"Vertex lists must have same length: {len(start_value.outer)} != {len(end_value.outer)}. "
                    f"Ensure both states have the same num_vertices parameter."
                )

            # Force closure ONLY if BOTH states are closed
            start_closed = getattr(
                start_state, "closed", True
            )  # Default True for closed shapes
            end_closed = getattr(end_state, "closed", True)

            # Interpolate outer vertices
            # NOTE: Path functions are NOT applied to vertices during morphing
            # They only apply to top-level Point2D fields like "pos"
            outer_buffer = vertex_buffer[0] if vertex_buffer else None
            interpolated_vertices = self._interpolate_vertex_list(
                start_value.outer.vertices,
                end_value.outer.vertices,
                eased_t,
                buffer=outer_buffer,
                ensure_closure=(start_closed and end_closed),
                path_func=None,
            )

            # Interpolate  vertex_loops
            interpolated_vertex_loops = []
            start_vertex_loops = start_value.holes
            end_vertex_loops = end_value.holes

            # vertex loops should have been matched during alignment, so counts should match
            if len(start_vertex_loops) != len(end_vertex_loops):
                # Fallback: if counts don't match, just use start or end based on t
                logger.warning(
                    f"Hole count mismatch during interpolation: {len(start_vertex_loops )} != {len(end_vertex_loops )}. "
                    f"This should not happen if vertex alignment was performed correctly. "
                    f"Using step interpolation at t=0.5 as fallback."
                )
                interpolated_vertex_loops = (
                    start_vertex_loops if eased_t < 0.5 else end_vertex_loops
                )
            else:
                # Interpolate each matched hole pair
                for hole_idx, (hole1, hole2) in enumerate(
                    zip(start_vertex_loops, end_vertex_loops)
                ):
                    if len(hole1.vertices) != len(hole2.vertices):
                        # If vertex counts don't match, just switch at t=0.5
                        logger.warning(
                            f"Hole {hole_idx} vertex count mismatch: {len(hole1.vertices)} != {len(hole2.vertices)}. "
                            f"This should not happen if hole alignment was performed correctly. "
                            f"Using step interpolation at t=0.5 as fallback."
                        )
                        interpolated_vertex_loops.append(
                            hole1 if eased_t < 0.5 else hole2
                        )
                    else:
                        # Interpolate hole vertices
                        hole_buffers = vertex_buffer[1] if vertex_buffer else []
                        hole_buffer = (
                            hole_buffers[hole_idx]
                            if (vertex_buffer and hole_idx < len(hole_buffers))
                            else None
                        )
                        interp_hole_verts = self._interpolate_vertex_list(
                            hole1.vertices,
                            hole2.vertices,
                            eased_t,
                            buffer=hole_buffer,
                            ensure_closure=True,  # Holes always closed
                            path_func=None,  # Path functions don't apply to vertices
                        )

                        interpolated_vertex_loops.append(
                            VertexLoop(interp_hole_verts, closed=True)
                        )

            # Return a VertexContours object with interpolated outer and  vertex_loops
            return VertexContours(
                outer=VertexLoop(
                    interpolated_vertices, closed=start_closed and end_closed
                ),
                holes=(
                    interpolated_vertex_loops if interpolated_vertex_loops else None
                ),
            )

        # 1. State interpolation (for clip_state, mask_state, and recursive calls)
        if isinstance(start_value, State) and isinstance(end_value, State):

            # Check if this is a morph between different VertexState types
            from svan2d.component.state.base_vertex import VertexState

            if (
                isinstance(start_value, VertexState)
                and isinstance(end_value, VertexState)
                and start_value.need_morph(end_value)
            ):
                # Need to align vertices for morphing
                from svan2d.transition.align_vertices import get_aligned_vertices

                contours1_aligned, contours2_aligned = get_aligned_vertices(
                    start_value,
                    end_value,
                    vertex_aligner=vertex_aligner,
                    mapper=mapper,
                )

                start_value = replace(start_value, _aligned_contours=contours1_aligned)
                end_value = replace(end_value, _aligned_contours=contours2_aligned)

            # Recursively interpolate the clip/mask state
            # Re-wrap mapper/aligner for recursive call
            morphing_config = None
            if mapper is not None or vertex_aligner is not None:
                from svan2d.velement.morphing import MorphingConfig

                morphing_config = MorphingConfig(
                    mapper=mapper, vertex_aligner=vertex_aligner
                )

            return self.create_eased_state(
                start_value,
                end_value,
                eased_t,
                segment_easing_overrides=None,
                attribute_keystates_fields=set(),
                vertex_buffer=None,
                segment_path_config=None,
                morphing_config=morphing_config,
            )

        # Handle State ↔ None transitions
        if (
            isinstance(start_value, Gradient)
            or isinstance(start_value, Pattern)
            or isinstance(start_value, Filter)
        ):
            return start_value.interpolate(end_value, eased_t)

        if isinstance(start_value, State) and end_value is None:
            # Fade out: opacity → 0
            return replace(start_value, opacity=lerp(start_value.opacity, 0.0, eased_t))
        if start_value is None and isinstance(end_value, State):
            # Fade in: opacity from 0
            return replace(end_value, opacity=lerp(0.0, end_value.opacity, eased_t))

        # 2. Point2D interpolation (with path function support and 2D easing)
        if isinstance(start_value, Point2D):
            # Check for path function for this specific field
            if self.path_resolver and segment_path_config is not None:
                path_func = self.path_resolver.get_path_for_field(
                    field_name, segment_path_config
                )
                # Only use path if one was configured for this field
                if segment_path_config.get(field_name) is not None:
                    # Convert 2D easing to scalar by averaging if needed
                    scalar_t = (
                        eased_t
                        if isinstance(eased_t, (int, float))
                        else (eased_t[0] + eased_t[1]) / 2
                    )
                    return path_func(start_value, end_value, scalar_t)
            # 2D easing (when no explicit path set for this field)
            if isinstance(eased_t, tuple):
                tx, ty = eased_t
                return Point2D(
                    lerp(start_value.x, end_value.x, tx),
                    lerp(start_value.y, end_value.y, ty),
                )
            else:
                # Standard linear interpolation
                return start_value.lerp(end_value, eased_t)

        # 3. SVG Path interpolation
        if isinstance(start_value, SVGPath):
            return self._interpolate_path(start_state, start_value, end_value, eased_t)

        # 4. Color interpolation
        if isinstance(start_value, Color):
            return start_value.interpolate(end_value, eased_t)

        # 5. Angle interpolation (handles wraparound)
        if self._is_angle_field(start_state, field_name):
            # Extract scalar if 2D easing used on angle field
            scalar_t = (
                eased_t
                if isinstance(eased_t, (int, float))
                else (eased_t[0] + eased_t[1]) / 2
            )
            return angle(start_value, end_value, scalar_t)

        # 6. Numeric interpolation
        if isinstance(start_value, (int, float)):
            # Extract scalar if 2D easing used on numeric field
            scalar_t = (
                eased_t
                if isinstance(eased_t, (int, float))
                else (eased_t[0] + eased_t[1]) / 2
            )
            return lerp(start_value, end_value, scalar_t)

        # 7. Non-numeric values: step function at t=0.5
        # Extract scalar if 2D easing used on non-numeric field
        scalar_t = (
            eased_t
            if isinstance(eased_t, (int, float))
            else (eased_t[0] + eased_t[1]) / 2
        )
        return step(start_value, end_value, scalar_t)

    def _interpolate_path(
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
        if self._path_is_closed(start_path):
            return FlubberMorpher.for_paths(start_path, end_path)(eased_t)
        else:
            return NativeMorpher.for_paths(start_path, end_path)(eased_t)

    def _is_angle_field(self, state: State, field_name: str) -> bool:
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

    def _path_is_closed(self, path: SVGPath, tolerance: float = 0.01) -> bool:
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
            (end_cmd.x - start_cmd.x) ** 2 + (end_cmd.y - start_cmd.y) ** 2
        ) ** 0.5

        return distance <= tolerance

    def _interpolate_vertex_list(
        self,
        vertices1: Points2D,
        vertices2: Points2D,
        eased_t: float,
        buffer: Optional[Points2D] = None,
        ensure_closure: bool = False,
        path_func=None,
    ) -> Points2D:
        """Interpolate between two vertex lists with optional buffer optimization

        Args:
            vertices1: Start vertices
            vertices2: End vertices (must match length)
            eased_t: Interpolation parameter
            buffer: Optional pre-allocated buffer for in-place operations
            ensure_closure: If True, force last vertex to equal first
            path_func: Optional path function for Point2D interpolation

        Returns:
           Points2D
        """
        if len(vertices1) != len(vertices2):
            raise ValueError(
                f"Vertex lists must have same length: {len(vertices1)} != {len(vertices2)}"
            )

        if buffer:
            # Optimized path: Use pre-allocated buffer with in-place operations
            num_verts = len(vertices1)

            # Resize buffer if needed (grow only, never shrink)
            if len(buffer) < num_verts:
                from svan2d.core.point2d import Point2D

                buffer.extend(Point2D(0.0, 0.0) for _ in range(num_verts - len(buffer)))

            # Interpolation with path function support
            for i, (v1, v2) in enumerate(zip(vertices1, vertices2)):
                if path_func:
                    buffer[i] = path_func(v1, v2, eased_t)
                else:
                    buffer[i] = v1.lerp(v2, eased_t)

            interpolated_vertices = buffer[:num_verts]
        else:
            # Fallback: Original behavior with path function support
            if path_func:
                interpolated_vertices = [
                    path_func(v1, v2, eased_t) for v1, v2 in zip(vertices1, vertices2)
                ]
            else:
                interpolated_vertices = [
                    v1.lerp(v2, eased_t) for v1, v2 in zip(vertices1, vertices2)
                ]

        # Ensure closure if requested
        if ensure_closure and len(interpolated_vertices) > 1:
            interpolated_vertices[-1] = interpolated_vertices[0]

        return interpolated_vertices
