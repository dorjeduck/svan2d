"""Morphing configuration for vertex state transitions.

Specifies strategies for M→N shape matching and vertex alignment during morphing.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MorphingConfig:
    """Morphing strategy configuration for shape transitions

    Specifies strategies for mapping items and aligning vertices during morphing.
    Used in KeyState to override default morphing behavior for specific transitions.

    Args:
        mapper: Strategy for M→N mapping (works for both states and holes)
               (SimpleMapper, GreedyMapper, ClusteringMapper)
        vertex_aligner: Strategy for aligning vertices within matched shapes
                       (AngularAligner, EuclideanAligner, SequentialAligner, etc.)

    Examples:
        Simple crossfade (no morphing):
        from svan2d.transition.mapping import SimpleMapper
        MorphingConfig(mapper=SimpleMapper())

        Greedy nearest-neighbor matching:
        from svan2d.transition.mapping import GreedyMapper
        MorphingConfig(mapper=GreedyMapper())

        Full configuration:
        MorphingConfig(
        ...     mapper=ClusteringMapper(),
        ...     vertex_aligner=AngularAligner()
        ... )
    """

    mapper: Optional[Any] = None  # Mapper type (avoid circular import)
    vertex_aligner: Optional[Any] = None  # VertexAligner type (avoid circular import)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict format for internal processing"""
        result = {}
        if self.mapper is not None:
            result["mapper"] = self.mapper
        if self.vertex_aligner is not None:
            result["vertex_aligner"] = self.vertex_aligner
        return result

    def __repr__(self):
        parts = []
        if self.mapper is not None:
            parts.append(f"mapper={self.mapper.__class__.__name__}")
        if self.vertex_aligner is not None:
            parts.append(f"vertex_aligner={self.vertex_aligner.__class__.__name__}")
        return f"MorphingConfig({', '.join(parts)})"
