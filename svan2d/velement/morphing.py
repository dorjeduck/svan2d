from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Morphing:
    """Morphing strategy configuration for vertex-based shape transitions

    Specifies strategies for mapping and aligning vertices during shape morphing.
    Used in KeyState to override default morphing behavior for specific transitions.

    Args:
        vertex_loop_mapper: Strategy for mapping vertex loops between states (SimpleMapper,
                    GreedyNearestMapper, DiscreteMapper, ClusteringMapper, etc.)
        vertex_aligner: Strategy for aligning vertices within matched shapes
                       (AngularAligner, EuclideanAligner, SequentialAligner, etc.)

    Examples:
        Hole mapping only:
        >>> Morphing(vertex_loop_mapper=SimpleMapper())

        Both hole mapping and vertex alignment:
        >>> Morphing(
        ...     vertex_loop_mapper=DiscreteMapper(),
        ...     vertex_aligner=EuclideanAligner()
        ... )

        Usage in KeyState:
        >>> KeyState(
        ...     state=perforated_state,
        ...     time=0.5,
        ...     morphing=Morphing(vertex_loop_mapper=ClusteringMapper())
        ... )
    """

    vertex_loop_mapper: Optional[Any] = None  # HoleMapper type (avoid circular import)
    vertex_aligner: Optional[Any] = None  # VertexAligner type (avoid circular import)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict format for internal processing

        Returns dict with 'vertex_loop_mapper' and 'vertex_aligner' keys for backward compatibility.
        """
        result = {}
        if self.vertex_loop_mapper is not None:
            result["vertex_loop_mapper"] = self.vertex_loop_mapper
        if self.vertex_aligner is not None:
            result["vertex_aligner"] = self.vertex_aligner
        return result
