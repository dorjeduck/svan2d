"""Interpolator for VertexContours (aligned vertices for morphing)."""

import logging
from typing import List, Optional, Tuple

from svan2d.component.state.base import State
from svan2d.component.vertex.vertex_contours import VertexContours
from svan2d.component.vertex.vertex_loop import VertexLoop
from svan2d.core.point2d import Points2D

logger = logging.getLogger(__name__)


class VertexContoursInterpolator:
    """Handles interpolation of VertexContours (outer contour + holes)."""

    def interpolate(
        self,
        start_state: State,
        end_state: State,
        start_value: VertexContours,
        end_value: VertexContours,
        eased_t: float,
        vertex_buffer: Optional[Tuple[List, List[List]]] = None,
    ) -> VertexContours:
        """
        Interpolate between two VertexContours.

        Args:
            start_state: Start state (for closed attribute)
            end_state: End state (for closed attribute)
            start_value: Starting VertexContours
            end_value: Ending VertexContours
            eased_t: Eased interpolation parameter (0.0 to 1.0)
            vertex_buffer: Optional reusable buffer (outer_buffer, hole_buffers)

        Returns:
            Interpolated VertexContours
        """
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
        start_closed = getattr(start_state, "closed", True)
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
        )

        # Interpolate vertex_loops (holes)
        interpolated_vertex_loops = self._interpolate_holes(
            start_value.holes,
            end_value.holes,
            eased_t,
            vertex_buffer,
        )

        # Return a VertexContours object with interpolated outer and vertex_loops
        return VertexContours(
            outer=VertexLoop(
                interpolated_vertices, closed=start_closed and end_closed
            ),
            holes=interpolated_vertex_loops if interpolated_vertex_loops else None,
        )

    def _interpolate_holes(
        self,
        start_holes: Optional[List[VertexLoop]],
        end_holes: Optional[List[VertexLoop]],
        eased_t: float,
        vertex_buffer: Optional[Tuple[List, List[List]]] = None,
    ) -> List[VertexLoop]:
        """Interpolate hole vertex loops."""
        interpolated_vertex_loops = []
        start_vertex_loops = start_holes or []
        end_vertex_loops = end_holes or []

        # Hole counts should have been matched during alignment
        if len(start_vertex_loops) != len(end_vertex_loops):
            logger.warning(
                f"Hole count mismatch during interpolation: {len(start_vertex_loops)} != {len(end_vertex_loops)}. "
                f"This should not happen if vertex alignment was performed correctly. "
                f"Using step interpolation at t=0.5 as fallback."
            )
            return start_vertex_loops if eased_t < 0.5 else end_vertex_loops

        # Interpolate each matched hole pair
        for hole_idx, (hole1, hole2) in enumerate(
            zip(start_vertex_loops, end_vertex_loops)
        ):
            if len(hole1.vertices) != len(hole2.vertices):
                logger.warning(
                    f"Hole {hole_idx} vertex count mismatch: {len(hole1.vertices)} != {len(hole2.vertices)}. "
                    f"This should not happen if hole alignment was performed correctly. "
                    f"Using step interpolation at t=0.5 as fallback."
                )
                interpolated_vertex_loops.append(hole1 if eased_t < 0.5 else hole2)
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
                )
                interpolated_vertex_loops.append(
                    VertexLoop(interp_hole_verts, closed=True)
                )

        return interpolated_vertex_loops

    def _interpolate_vertex_list(
        self,
        vertices1: Points2D,
        vertices2: Points2D,
        eased_t: float,
        buffer: Optional[Points2D] = None,
        ensure_closure: bool = False,
    ) -> Points2D:
        """Interpolate between two vertex lists with optional buffer optimization.

        Args:
            vertices1: Start vertices
            vertices2: End vertices (must match length)
            eased_t: Interpolation parameter
            buffer: Optional pre-allocated buffer for in-place operations
            ensure_closure: If True, force last vertex to equal first

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

            # Interpolation
            for i, (v1, v2) in enumerate(zip(vertices1, vertices2)):
                buffer[i] = v1.lerp(v2, eased_t)

            interpolated_vertices = buffer[:num_verts]
        else:
            # Fallback: Original behavior
            interpolated_vertices = [
                v1.lerp(v2, eased_t) for v1, v2 in zip(vertices1, vertices2)
            ]

        # Ensure closure if requested
        if ensure_closure and len(interpolated_vertices) > 1:
            interpolated_vertices[-1] = interpolated_vertices[0]

        return interpolated_vertices
