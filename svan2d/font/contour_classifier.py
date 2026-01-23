"""Classify glyph contours as outer boundaries, holes, or disconnected components"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from svan2d.component.vertex.vertex_contours import VertexContours
from svan2d.component.vertex.vertex_loop import VertexLoop
from svan2d.core.point2d import Point2D, Points2D

from .bezier_sampler import (
    estimate_cubic_arc_length,
    estimate_line_arc_length,
    estimate_quadratic_arc_length,
    resample_to_vertex_count,
    sample_cubic_arc_length,
    sample_quadratic_arc_length,
)
from .glyph_extractor import BezierSegment, GlyphContour, GlyphOutline


@dataclass
class ClassifiedContour:
    """A contour with classification info"""

    vertices: Points2D
    area: float  # Signed area (positive = CCW, negative = CW)
    bounds: Tuple[float, float, float, float]  # xMin, yMin, xMax, yMax
    is_hole: bool  # True if this is a hole (inside another contour)
    parent_index: Optional[int]  # Index of containing contour, if hole


def contour_to_vertices(contour: GlyphContour, samples_per_segment: int = 10) -> Points2D:
    """Convert a GlyphContour to vertices by sampling bezier segments.

    Args:
        contour: GlyphContour with bezier segments
        samples_per_segment: Base samples per bezier segment

    Returns:
        List of Point2D vertices
    """
    if contour.is_empty():
        return []

    all_points = []

    # Find the starting point - the end of the last segment (closed loop start)
    if not contour.segments:
        return []

    last_seg = contour.segments[-1]
    current_pos = last_seg.points[-1]

    for segment in contour.segments:
        if segment.type == "line":
            # Line segment - add start point, then update position
            all_points.append(current_pos)
            current_pos = segment.points[0]

        elif segment.type == "qcurve":
            # Quadratic bezier
            if len(segment.points) == 1:
                # Degenerate - treat as line
                all_points.append(current_pos)
                current_pos = segment.points[0]
            else:
                ctrl = segment.points[0]
                end = segment.points[1]
                # Estimate arc length to determine sample count
                arc_len = estimate_quadratic_arc_length(current_pos, ctrl, end)
                num_samples = max(2, int(arc_len / 10) + 1)  # Adaptive sampling
                num_samples = min(num_samples, samples_per_segment * 3)
                samples = sample_quadratic_arc_length(current_pos, ctrl, end, num_samples)
                all_points.extend(samples)
                current_pos = end

        elif segment.type == "curve":
            # Cubic bezier
            if len(segment.points) < 3:
                # Degenerate
                all_points.append(current_pos)
                if segment.points:
                    current_pos = segment.points[-1]
            else:
                ctrl1 = segment.points[0]
                ctrl2 = segment.points[1]
                end = segment.points[2]
                # Estimate arc length to determine sample count
                arc_len = estimate_cubic_arc_length(current_pos, ctrl1, ctrl2, end)
                num_samples = max(2, int(arc_len / 10) + 1)
                num_samples = min(num_samples, samples_per_segment * 3)
                samples = sample_cubic_arc_length(current_pos, ctrl1, ctrl2, end, num_samples)
                all_points.extend(samples)
                current_pos = end

    return all_points


def calculate_signed_area(vertices: Points2D) -> float:
    """Calculate signed area of a polygon.

    Positive = counter-clockwise winding
    Negative = clockwise winding
    """
    if len(vertices) < 3:
        return 0.0

    area = 0.0
    n = len(vertices)
    for i in range(n):
        j = (i + 1) % n
        area += vertices[i].x * vertices[j].y
        area -= vertices[j].x * vertices[i].y
    return area / 2.0


def calculate_bounds(vertices: Points2D) -> Tuple[float, float, float, float]:
    """Calculate bounding box of vertices."""
    if not vertices:
        return (0, 0, 0, 0)
    xs = [v.x for v in vertices]
    ys = [v.y for v in vertices]
    return (min(xs), min(ys), max(xs), max(ys))


def point_in_polygon(point: Point2D, polygon: Points2D) -> bool:
    """Test if a point is inside a polygon using ray casting."""
    n = len(polygon)
    if n < 3:
        return False

    inside = False
    j = n - 1

    for i in range(n):
        pi = polygon[i]
        pj = polygon[j]

        if ((pi.y > point.y) != (pj.y > point.y)) and (
            point.x < (pj.x - pi.x) * (point.y - pi.y) / (pj.y - pi.y) + pi.x
        ):
            inside = not inside
        j = i

    return inside


def bounds_contains(outer: Tuple[float, float, float, float], inner: Tuple[float, float, float, float]) -> bool:
    """Check if outer bounds fully contain inner bounds."""
    return (
        outer[0] <= inner[0]
        and outer[1] <= inner[1]
        and outer[2] >= inner[2]
        and outer[3] >= inner[3]
    )


def classify_contours(outline: GlyphOutline, num_vertices: int) -> List[VertexContours]:
    """Classify contours and build VertexContours objects.

    This identifies which contours are outer boundaries vs holes,
    and groups them appropriately. Disconnected components become
    separate VertexContours objects.

    Args:
        outline: GlyphOutline from glyph extraction
        num_vertices: Target vertex count per contour

    Returns:
        List of VertexContours (one per disconnected component)
    """
    if outline.is_empty():
        return []

    # Step 1: Convert all contours to vertices and compute properties
    classified = []
    for contour in outline.contours:
        vertices = contour_to_vertices(contour)
        if len(vertices) < 3:
            continue

        # Resample to target vertex count
        vertices = resample_to_vertex_count(vertices, num_vertices)

        area = calculate_signed_area(vertices)
        bounds = calculate_bounds(vertices)

        classified.append(
            ClassifiedContour(
                vertices=vertices,
                area=area,
                bounds=bounds,
                is_hole=False,  # Will be determined below
                parent_index=None,
            )
        )

    if not classified:
        return []

    # Step 2: Determine containment relationships
    # A contour is a hole if:
    # 1. It has opposite winding to its containing contour
    # 2. Its centroid is inside another contour

    for i, inner in enumerate(classified):
        inner_centroid = Point2D(
            sum(v.x for v in inner.vertices) / len(inner.vertices),
            sum(v.y for v in inner.vertices) / len(inner.vertices),
        )

        # Find the smallest containing contour
        smallest_container_idx = None
        smallest_container_area = float("inf")

        for j, outer in enumerate(classified):
            if i == j:
                continue

            # Quick bounds check
            if not bounds_contains(outer.bounds, inner.bounds):
                continue

            # Check if centroid is inside
            if point_in_polygon(inner_centroid, outer.vertices):
                if abs(outer.area) < smallest_container_area:
                    smallest_container_area = abs(outer.area)
                    smallest_container_idx = j

        if smallest_container_idx is not None:
            # This contour is inside another
            # It's a hole if it has opposite winding to its parent
            parent = classified[smallest_container_idx]
            if (inner.area > 0) != (parent.area > 0):
                inner.is_hole = True
                inner.parent_index = smallest_container_idx

    # Step 3: Build VertexContours objects
    # Group outer contours with their holes
    result = []

    # Process outer contours (not holes)
    for i, contour in enumerate(classified):
        if contour.is_hole:
            continue

        # Find all holes belonging to this outer
        holes = []
        for j, other in enumerate(classified):
            if other.is_hole and other.parent_index == i:
                # Ensure hole has correct winding (clockwise = negative area)
                hole_vertices = other.vertices
                if other.area > 0:
                    # Reverse to make clockwise
                    hole_vertices = list(reversed(hole_vertices))
                holes.append(VertexLoop(hole_vertices, closed=True))

        # Ensure outer has correct winding (counter-clockwise = positive area)
        outer_vertices = contour.vertices
        if contour.area < 0:
            # Reverse to make counter-clockwise
            outer_vertices = list(reversed(outer_vertices))

        outer_loop = VertexLoop(outer_vertices, closed=True)
        result.append(VertexContours(outer_loop, holes if holes else None))

    return result
