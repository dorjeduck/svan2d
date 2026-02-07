"""State classes for various shapes and elements.

States are immutable dataclasses that define geometry and visual attributes.
Each state type has a corresponding renderer (e.g., CircleState → CircleRenderer).
"""

from .arc import ArcState
from .arrow import ArrowState
from .astroid import AstroidState
from .base import State, States
from .base_color import ColorState
from .base_vertex import VertexState
from .circle import CircleState
from .circle_text import CircleTextState
from .cross import CrossState
from .ellipse import EllipseState
from .flower import FlowerState
from .heart import HeartState
from .infinity import InfinityState
from .line import LineState
from .number import NumberFormat, NumberState, Rounding
from .path import PathState
from .path_and_text_variants import PathAndTextVariantsState
from .path_text import PathTextState
from .perforated import (
    Astroid,
    Circle,
    Ellipse,
    PerforatedCircleState,
    PerforatedEllipseState,
    PerforatedPolygonState,
    PerforatedRectangleState,
    PerforatedStarState,
    PerforatedTriangleState,
    PerforatedVertexState,
    Polygon,
    Rectangle,
    Shape,
    Star,
)
from .point import PointState
from .poly_ring import PolyRingState
from .polygon import PolygonState
from .radial_segments import RadialSegmentsState
from .raw_svg import RawSvgState
from .rectangle import RectangleState
from .ring import RingState
from .spiral import SpiralState
from .square import SquareState
from .square_ring import SquareRingState
from .star import StarState
from .state_collection import StateCollectionState
from .text import TextRendering, TextState
from .text_path import TextPathState
from .triangle import TriangleState
from .wave import WaveState

__all__ = [
    "State",
    "States",
    "ColorState",
    "VertexState",
    "ArcState",
    "ArrowState",
    "AstroidState",
    "CircleTextState",
    "CircleState",
    "CrossState",
    "EllipseState",
    "LineState",
    "NumberFormat",
    "NumberState",
    "Rounding",
    "PathState",
    "PointState",
    "PerforatedVertexState",
    "PerforatedCircleState",
    "PerforatedStarState",
    "PerforatedEllipseState",
    "PerforatedRectangleState",
    "PerforatedPolygonState",
    "PerforatedTriangleState",
    "Shape",
    "Circle",
    "Ellipse",
    "Rectangle",
    "Polygon",
    "Star",
    "Astroid",
    "PathTextState",
    "PathAndTextVariantsState",
    "PolygonState",
    "PolyRingState",
    "RadialSegmentsState",
    "RawSvgState",
    "RectangleState",
    "RingState",
    "SquareState",
    "SquareRingState",
    "StarState",
    "TextPathState",
    "TextRendering",
    "TextState",
    "TriangleState",
    "FlowerState",
    "HeartState",
    "InfinityState",
    "SpiralState",
    "WaveState",
    "StateCollectionState",
]
