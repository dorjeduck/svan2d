"""Vertex alignment and preprocessing for morph interpolation

This module orchestrates vertex alignment logic that happens once per
morph segment during keystate preprocessing. The alignment is stored
directly in the state via the _aligned_contours field.

This is the main entry point - uses pluggable strategies from:
- vertex_alignment/: Strategies for aligning outer vertex loops
- mapping/: Generic mapper for matching holes (M→N)
"""

from __future__ import annotations
from typing import Tuple, Optional, TYPE_CHECKING

from svan2d.component.vertex import VertexContours, VertexLoop
from svan2d.config import get_config, ConfigKey

from .vertex_alignment import (
    VertexAligner,
    get_aligner,
    AlignmentContext,
    AngularAligner,
)
from .mapping import Mapper, GreedyMapper, ClusteringMapper, SimpleMapper

from svan2d.component.state.base_vertex import VertexState


def _get_mapper_from_config() -> Mapper:
    """Get mapper instance based on config settings

    Returns:
        Mapper instance configured from svan2d.toml settings
    """
    config = get_config()
    strategy = config.get(ConfigKey.MORPHING_VERTEX_LOOP_MAPPER, "greedy")

    if strategy == "greedy":
        return GreedyMapper()
    elif strategy == "clustering":
        max_iter = config.get(ConfigKey.MORPHING_CLUSTERING_MAX_ITERATIONS, 50)
        seed = config.get(ConfigKey.MORPHING_CLUSTERING_RANDOM_SEED, 42)
        return ClusteringMapper(max_iterations=max_iter, random_seed=seed)
    elif strategy == "simple":
        return SimpleMapper()
    else:
        # Default to greedy for unknown strategies
        return GreedyMapper()


def get_aligned_vertices(
    state1: VertexState,
    state2: VertexState,
    vertex_aligner: Optional[VertexAligner] = None,
    mapper: Optional[Mapper] = None,
    rotation_target: Optional[float] = None,
) -> Tuple[VertexContours, VertexContours]:
    """Align vertex contours and return aligned contours

    This is called once per segment during keystate preprocessing.
    Returns new VertexContours instances with aligned outer vertices
    and matched holes.

    Uses pluggable strategies:
    - VertexAligner: How to align outer vertex loops (auto-selected by default)
    - Mapper: How to match holes between states (from config by default)

    Args:
        state1: First state in the transition
        state2: Second state in the transition
        vertex_aligner: Custom vertex alignment strategy (default: auto-select based on closure)
        mapper: Custom mapper for hole matching (default: from config)
        rotation_target: Target rotation for dynamic alignment (default: None, uses state2.rotation)

    Returns:
        Tuple of (contours1_aligned, contours2_aligned)

    Raises:
        ValueError: If states have different num_vertices
    """
    if state1._num_vertices != state2._num_vertices:
        raise ValueError(
            f"Cannot morph shapes with different num_points: "
            f"{state1._num_vertices} != {state2._num_vertices}. "
            f"Both shapes must have the same vertex resolution."
        )

    # Get raw contours (using _generate_contours to avoid recursion)
    contours1 = state1._generate_contours()
    contours2 = state2._generate_contours()

    # Select strategies (use defaults if not provided)
    if vertex_aligner is None:
        vertex_aligner = get_aligner(state1.closed, state2.closed)

    if mapper is None:
        mapper = _get_mapper_from_config()

    # Align outer vertices
    context = AlignmentContext(
        rotation1=state1.rotation,
        rotation2=state2.rotation,
        closed1=state1.closed,
        closed2=state2.closed,
    )
    verts1_aligned, verts2_aligned = vertex_aligner.align(
        contours1.outer.vertices,
        contours2.outer.vertices,
        context,
        rotation_target=rotation_target,
    )

    # Match holes using the mapper with centroid as position
    holes1 = contours1.holes if contours1.holes else []
    holes2 = contours2.holes if contours2.holes else []

    matches = mapper.map(holes1, holes2, lambda h: h.centroid())

    # Align vertices within each matched hole pair
    aligned_holes1 = []
    aligned_holes2 = []

    # Create a hole-specific aligner (always use angular for closed holes)
    hole_aligner = AngularAligner()
    hole_context = AlignmentContext(
        rotation1=0, rotation2=0, closed1=True, closed2=True
    )

    for match in matches:
        if match.is_morph:
            # Both holes exist - align them
            h1_verts = match.start.vertices
            h2_verts = match.end.vertices

            if len(h1_verts) == len(h2_verts) and len(h1_verts) > 0:
                h1_aligned, h2_aligned = hole_aligner.align(
                    h1_verts, h2_verts, hole_context
                )
                aligned_holes1.append(VertexLoop(h1_aligned, closed=True))
                aligned_holes2.append(VertexLoop(h2_aligned, closed=True))
            else:
                aligned_holes1.append(match.start)
                aligned_holes2.append(match.end)

        elif match.is_destruction:
            # Hole disappears - create zero-hole at same position
            hole = match.start
            zero_hole = _create_zero_hole(hole)
            aligned_holes1.append(hole)
            aligned_holes2.append(zero_hole)

        elif match.is_creation:
            # Hole appears - create zero-hole at target position
            hole = match.end
            zero_hole = _create_zero_hole(hole)
            aligned_holes1.append(zero_hole)
            aligned_holes2.append(hole)

    # Create new VertexContours with aligned outer loops and aligned holes
    contours1_aligned = VertexContours(
        outer=VertexLoop(verts1_aligned, closed=contours1.outer.closed),
        holes=aligned_holes1 if aligned_holes1 else None,
    )
    contours2_aligned = VertexContours(
        outer=VertexLoop(verts2_aligned, closed=contours2.outer.closed),
        holes=aligned_holes2 if aligned_holes2 else None,
    )

    return contours1_aligned, contours2_aligned


def _create_zero_hole(hole: VertexLoop) -> VertexLoop:
    """Create a zero-sized hole at the centroid of the original hole.

    Used for hole creation/destruction animations.
    """
    centroid = hole.centroid()
    # Create a degenerate hole with all vertices at the centroid
    zero_vertices = [centroid for _ in hole.vertices]
    return VertexLoop(zero_vertices, closed=True)
