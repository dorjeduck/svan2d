"""VertexRectangle - rectangle as a VertexLoop"""

from __future__ import annotations

import math

from svan2d.core.point2d import Point2D

from .vertex_loop import VertexLoop


class VertexRectangle(VertexLoop):
    """Rectangle as a VertexLoop

    Generates a rectangle with vertices distributed along its perimeter.
    Supports rounded corners via corner_radius parameter.
    The num_vertices parameter is crucial for morphing - shapes with the same
    num_vertices can morph smoothly between each other.
    """

    def __init__(
        self,
        center: Point2D = Point2D(0, 0),
        width: float = 100.0,
        height: float = 100.0,
        num_vertices: int = 128,
        corner_radius: float = 0.0,
    ):
        """Create a rectangle as a vertex loop

        Args:
            center: Center point of rectangle
            width: Rectangle width
            height: Rectangle height
            num_vertices: Number of vertices distributed along perimeter (important for morphing!)
            corner_radius: Radius for rounded corners (0 = sharp corners)
        """
        if num_vertices < 4:
            raise ValueError("Rectangle requires at least 4 vertices")

        # Clamp corner_radius to maximum valid value (creates capsule/stadium)
        max_radius = min(width, height) / 2
        r = min(corner_radius, max_radius) if corner_radius > 0 else 0.0

        # Use simple algorithm for sharp corners
        if r == 0:
            vertices = self._generate_sharp_corners(center, width, height, num_vertices)
        else:
            vertices = self._generate_rounded_corners(
                center, width, height, num_vertices, r
            )

        super().__init__(vertices, closed=True)

    def _generate_sharp_corners(
        self,
        center: Point2D,
        width: float,
        height: float,
        num_vertices: int,
    ) -> list[Point2D]:
        """Generate vertices for rectangle with sharp corners"""
        hw = width / 2
        hh = height / 2

        corners = [
            Point2D(center.x - hw, center.y - hh),  # Top-left
            Point2D(center.x + hw, center.y - hh),  # Top-right
            Point2D(center.x + hw, center.y + hh),  # Bottom-right
            Point2D(center.x - hw, center.y + hh),  # Bottom-left
        ]

        perimeter = 2 * (width + height)
        side_lengths = [width, height, width, height]

        vertices = []
        for i in range(num_vertices - 1):
            target_distance = (i / (num_vertices - 1)) * perimeter

            cumulative = 0.0
            for side_idx in range(4):
                if cumulative + side_lengths[side_idx] >= target_distance:
                    distance_along_side = target_distance - cumulative
                    start_corner = corners[side_idx]
                    end_corner = corners[(side_idx + 1) % 4]
                    t = distance_along_side / side_lengths[side_idx]

                    x = start_corner.x + t * (end_corner.x - start_corner.x)
                    y = start_corner.y + t * (end_corner.y - start_corner.y)
                    vertices.append(Point2D(x, y))
                    break
                cumulative += side_lengths[side_idx]

        vertices.append(vertices[0])
        return vertices

    def _generate_rounded_corners(
        self,
        center: Point2D,
        width: float,
        height: float,
        num_vertices: int,
        r: float,
    ) -> list[Point2D]:
        """Generate vertices for rectangle with rounded corners

        Segments are ordered starting from top-left corner, going clockwise:
        1. Top-left arc (from left edge to top edge)
        2. Top edge (straight)
        3. Top-right arc
        4. Right edge (straight)
        5. Bottom-right arc
        6. Bottom edge (straight)
        7. Bottom-left arc
        8. Left edge (straight)
        """
        hw = width / 2
        hh = height / 2

        # Arc centers (inset from corners by radius)
        arc_centers = [
            Point2D(center.x - hw + r, center.y - hh + r),  # Top-left
            Point2D(center.x + hw - r, center.y - hh + r),  # Top-right
            Point2D(center.x + hw - r, center.y + hh - r),  # Bottom-right
            Point2D(center.x - hw + r, center.y + hh - r),  # Bottom-left
        ]

        # Straight edge lengths (reduced by radius at each end)
        edge_h = width - 2 * r  # Horizontal edges (top and bottom)
        edge_v = height - 2 * r  # Vertical edges (left and right)

        # Arc length for each quarter circle
        arc_length = (math.pi / 2) * r

        # Total perimeter: 4 arcs + 4 straight edges
        perimeter = 4 * arc_length + 2 * edge_h + 2 * edge_v

        # Segment lengths in order: arc, edge, arc, edge, arc, edge, arc, edge
        segment_lengths = [
            arc_length,  # Top-left arc
            edge_h,  # Top edge
            arc_length,  # Top-right arc
            edge_v,  # Right edge
            arc_length,  # Bottom-right arc
            edge_h,  # Bottom edge
            arc_length,  # Bottom-left arc
            edge_v,  # Left edge
        ]

        # Starting angles for each arc (in radians, 0 = right, counter-clockwise)
        # We go clockwise, so angles decrease
        arc_start_angles = [
            math.pi,  # Top-left: starts pointing left (180°)
            math.pi / 2,  # Top-right: starts pointing up (90°)
            0,  # Bottom-right: starts pointing right (0°)
            -math.pi / 2,  # Bottom-left: starts pointing down (-90°)
        ]

        vertices = []
        for i in range(num_vertices - 1):
            target_distance = (i / (num_vertices - 1)) * perimeter

            cumulative = 0.0
            for seg_idx in range(8):
                seg_len = segment_lengths[seg_idx]
                if cumulative + seg_len >= target_distance:
                    distance_in_segment = target_distance - cumulative
                    t = distance_in_segment / seg_len if seg_len > 0 else 0

                    if seg_idx % 2 == 0:
                        # Arc segment
                        arc_idx = seg_idx // 2
                        arc_center = arc_centers[arc_idx]
                        start_angle = arc_start_angles[arc_idx]
                        # Clockwise rotation: subtract angle
                        angle = start_angle - t * (math.pi / 2)
                        x = arc_center.x + r * math.cos(angle)
                        y = arc_center.y - r * math.sin(angle)
                    else:
                        # Straight edge segment
                        edge_idx = seg_idx // 2
                        if edge_idx == 0:
                            # Top edge: left to right
                            x = center.x - hw + r + t * edge_h
                            y = center.y - hh
                        elif edge_idx == 1:
                            # Right edge: top to bottom
                            x = center.x + hw
                            y = center.y - hh + r + t * edge_v
                        elif edge_idx == 2:
                            # Bottom edge: right to left
                            x = center.x + hw - r - t * edge_h
                            y = center.y + hh
                        else:
                            # Left edge: bottom to top
                            x = center.x - hw
                            y = center.y + hh - r - t * edge_v

                    vertices.append(Point2D(x, y))
                    break
                cumulative += seg_len

        vertices.append(vertices[0])
        return vertices
