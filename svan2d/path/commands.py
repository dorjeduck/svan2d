# ============================================================================
# svan2d/paths/commands.py
# ============================================================================
"""SVG Path Command Classes"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from svan2d.core.point2d import Point2D


@dataclass
class PathCommand(ABC):
    """Abstract base class for SVG path commands"""

    @abstractmethod
    def to_string(self) -> str:
        """Convert command to SVG path string format"""
        pass

    @abstractmethod
    def to_absolute(self, current_pos: Point2D) -> PathCommand:
        """Convert to absolute coordinates"""
        pass

    @abstractmethod
    def get_end_point(self, current_pos: Point2D) -> Point2D:
        """Get the end point of this command"""
        pass

    @abstractmethod
    def interpolate(self, other: PathCommand, t: float) -> PathCommand:
        """Interpolate between this command and another at time t (0.0 to 1.0)"""
        pass


@dataclass
class MoveTo(PathCommand):
    """M or m command - Move to a point"""

    pos: Point2D
    absolute: bool = True

    def to_string(self) -> str:
        cmd = "M" if self.absolute else "m"
        return f"{cmd} {self.pos.x},{self.pos.y}"

    def to_absolute(self, current_pos: Point2D) -> MoveTo:
        if self.absolute:
            return self
        return MoveTo(current_pos + self.pos)

    def get_end_point(self, current_pos: Point2D) -> Point2D:
        if self.absolute:
            return self.pos
        return current_pos + self.pos

    def interpolate(self, other: PathCommand, t: float) -> MoveTo:
        if not isinstance(other, MoveTo):
            raise ValueError(f"Cannot interpolate MoveTo with {type(other).__name__}")
        return MoveTo(
            self.pos.lerp(other.pos, t),
            absolute=True,  # Interpolated path should use absolute
        )


@dataclass
class LineTo(PathCommand):
    """L or l command - Draw a line to a point"""

    pos: Point2D
    absolute: bool = True

    def to_string(self) -> str:
        cmd = "L" if self.absolute else "l"
        return f"{cmd} {self.pos.x},{self.pos.y}"

    def to_absolute(self, current_pos: Point2D) -> LineTo:
        if self.absolute:
            return self
        return LineTo(current_pos + self.pos)

    def get_end_point(self, current_pos: Point2D) -> Point2D:
        if self.absolute:
            return self.pos
        return current_pos + self.pos

    def interpolate(self, other: PathCommand, t: float) -> LineTo:
        if not isinstance(other, LineTo):
            raise ValueError(f"Cannot interpolate LineTo with {type(other).__name__}")
        return LineTo(
            self.pos.lerp(other.pos, t),
            absolute=True,
        )


# --- New Commands: Horizontal and Vertical Lines ---


@dataclass
class HorizontalLine(PathCommand):
    """H or h command - Draw a horizontal line to a new x coordinate"""

    x: float
    absolute: bool = True

    def to_string(self) -> str:
        cmd = "H" if self.absolute else "h"
        return f"{cmd} {self.x}"

    def to_absolute(self, current_pos: Point2D) -> LineTo:
        """Converts to a standard LineTo command with the current y-coordinate"""
        if self.absolute:
            return LineTo(Point2D(self.x, current_pos.y))
        return LineTo(Point2D(current_pos.x + self.x, current_pos.y))

    def get_end_point(self, current_pos: Point2D) -> Point2D:
        if self.absolute:
            return Point2D(self.x, current_pos.y)
        return Point2D(current_pos.x + self.x, current_pos.y)

    def interpolate(self, other: PathCommand, t: float) -> HorizontalLine:
        if not isinstance(other, HorizontalLine):
            raise ValueError(
                f"Cannot interpolate HorizontalLine with {type(other).__name__}"
            )
        return HorizontalLine(x=self.x + (other.x - self.x) * t, absolute=True)


@dataclass
class VerticalLine(PathCommand):
    """V or v command - Draw a vertical line to a new y coordinate"""

    y: float
    absolute: bool = True

    def to_string(self) -> str:
        cmd = "V" if self.absolute else "v"
        return f"{cmd} {self.y}"

    def to_absolute(self, current_pos: Point2D) -> LineTo:
        """Converts to a standard LineTo command with the current x-coordinate"""
        if self.absolute:
            return LineTo(Point2D(current_pos.x, self.y))
        return LineTo(Point2D(current_pos.x, current_pos.y + self.y))

    def get_end_point(self, current_pos: Point2D) -> Point2D:
        if self.absolute:
            return Point2D(current_pos.x, self.y)
        return Point2D(current_pos.x, current_pos.y + self.y)

    def interpolate(self, other: PathCommand, t: float) -> VerticalLine:
        if not isinstance(other, VerticalLine):
            raise ValueError(
                f"Cannot interpolate VerticalLine with {type(other).__name__}"
            )
        return VerticalLine(y=self.y + (other.y - self.y) * t, absolute=True)


# --- Bezier Curves ---


@dataclass
class QuadraticBezier(PathCommand):
    """Q or q command - Quadratic Bezier curve"""

    center: Point2D = Point2D(0, 0)
    pos: Point2D = Point2D(0, 0)
    absolute: bool = True

    def to_string(self) -> str:
        cmd = "Q" if self.absolute else "q"
        return f"{cmd} {self.center.x},{self.center.y} {self.pos.x},{self.pos.y}"

    def to_absolute(self, current_pos: Point2D) -> QuadraticBezier:
        if self.absolute:
            return self
        return QuadraticBezier(
            current_pos + self.center,
            current_pos + self.pos,
            absolute=True,
        )

    def get_end_point(self, current_pos: Point2D) -> Point2D:
        if self.absolute:
            return self.pos
        return current_pos + self.pos

    def interpolate(self, other: PathCommand, t: float) -> QuadraticBezier:
        if not isinstance(other, QuadraticBezier):
            raise ValueError(
                f"Cannot interpolate QuadraticBezier with {type(other).__name__}"
            )
        return QuadraticBezier(
            self.center.lerp(other.center, t), self.pos.lerp(other.pos, t), absolute=True
        )


@dataclass
class CubicBezier(PathCommand):
    """C or c command - Cubic Bezier curve"""

    center1: Point2D
    center2: Point2D
    pos: Point2D
    absolute: bool = True

    def to_string(self) -> str:
        cmd = "C" if self.absolute else "c"
        return f"{cmd} {self.center1.x},{self.center1.y} {self.center2.x},{self.center2.y} {self.pos.x},{self.pos.y}"

    def to_absolute(self, current_pos: Point2D) -> CubicBezier:
        if self.absolute:
            return self
        return CubicBezier(
            current_pos + self.center1,
            current_pos + self.center2,
            current_pos + self.pos,
            absolute=True,
        )

    def get_end_point(self, current_pos: Point2D) -> Point2D:
        if self.absolute:
            return self.pos
        return Point2D(current_pos.x + self.pos.x, current_pos.y + self.pos.y)

    def interpolate(self, other: PathCommand, t: float) -> CubicBezier:
        if not isinstance(other, CubicBezier):
            raise ValueError(
                f"Cannot interpolate CubicBezier with {type(other).__name__}"
            )
        return CubicBezier(
            self.center1.lerp(other.center1, t),
            self.center2.lerp(other.center2, t),
            self.pos.lerp(other.pos, t),
            absolute=True,
        )


# --- New Commands: Smooth Bezier Curves ---


@dataclass
class SmoothQuadraticBezier(PathCommand):
    """T or t command - Smooth Quadratic Bezier curve (T = QuadraticBezier with reflected control point)"""

    pos: Point2D
    absolute: bool = True

    def to_string(self) -> str:
        cmd = "T" if self.absolute else "t"
        return f"{cmd} {self.pos.x},{self.pos.y}"

    def to_absolute(self, current_pos: Point2D) -> SmoothQuadraticBezier:
        if self.absolute:
            return self
        return SmoothQuadraticBezier(
            pos=Point2D(current_pos.x + self.pos.x, current_pos.y + self.pos.y), absolute=True
        )

    def get_end_point(self, current_pos: Point2D) -> Point2D:
        if self.absolute:
            return self.pos
        return Point2D(current_pos.x + self.pos.x, current_pos.y + self.pos.y)

    def interpolate(self, other: PathCommand, t: float) -> SmoothQuadraticBezier:
        if not isinstance(other, SmoothQuadraticBezier):
            raise ValueError(
                f"Cannot interpolate SmoothQuadraticBezier with {type(other).__name__}"
            )
        return SmoothQuadraticBezier(
            self.pos.lerp(other.pos, t),
            absolute=True,
        )


@dataclass
class SmoothCubicBezier(PathCommand):
    """S or s command - Smooth Cubic Bezier curve (S = CubicBezier with reflected control point 1)"""

    center: Point2D
    pos: Point2D
    absolute: bool = True

    def to_string(self) -> str:
        cmd = "S" if self.absolute else "s"
        return f"{cmd} {self.center.x},{self.center.y} {self.pos.x},{self.pos.y}"

    def to_absolute(self, current_pos: Point2D) -> SmoothCubicBezier:
        if self.absolute:
            return self
        return SmoothCubicBezier(
            current_pos + self.center,
            current_pos + self.pos,
            absolute=True,
        )

    def get_end_point(self, current_pos: Point2D) -> Point2D:
        if self.absolute:
            return self.pos
        return Point2D(current_pos.x + self.pos.x, current_pos.y + self.pos.y)

    def interpolate(self, other: PathCommand, t: float) -> SmoothCubicBezier:
        if not isinstance(other, SmoothCubicBezier):
            raise ValueError(
                f"Cannot interpolate SmoothCubicBezier with {type(other).__name__}"
            )
        return SmoothCubicBezier(
            self.center.lerp(other.center, t),
            self.pos.lerp(other.pos, t),
            absolute=True,
        )


# --- New Command: Arc ---


@dataclass
class Arc(PathCommand):
    """A or a command - Elliptical Arc curve"""

    rx: float
    ry: float
    x_axis_rotation: float
    large_arc_flag: int
    sweep_flag: int
    pos: Point2D
    absolute: bool = True

    def to_string(self) -> str:
        cmd = "A" if self.absolute else "a"
        # Flags (large_arc_flag, sweep_flag) are 0 or 1 integers
        return (
            f"{cmd} {self.rx},{self.ry} {self.x_axis_rotation} "
            f"{self.large_arc_flag},{self.sweep_flag} {self.pos.x},{self.pos.y}"
        )

    def to_absolute(self, current_pos: Point2D) -> Arc:
        if self.absolute:
            return self
        return Arc(
            rx=self.rx,
            ry=self.ry,
            x_axis_rotation=self.x_axis_rotation,
            large_arc_flag=self.large_arc_flag,
            sweep_flag=self.sweep_flag,
            pos=Point2D(current_pos.x + self.pos.x, current_pos.y + self.pos.y),
            absolute=True,
        )

    def get_end_point(self, current_pos: Point2D) -> Point2D:
        if self.absolute:
            return self.pos
        return Point2D(current_pos.x + self.pos.x, current_pos.y + self.pos.y)

    def interpolate(self, other: PathCommand, t: float) -> Arc:
        if not isinstance(other, Arc):
            raise ValueError(f"Cannot interpolate Arc with {type(other).__name__}")

        # Interpolate all numeric parameters. Flags (0/1) are usually kept constant
        # during simple interpolation, or one path dominates for the whole morph.
        # We will interpolate them here, and rely on rounding/clamping later if needed.
        return Arc(
            rx=self.rx + (other.rx - self.rx) * t,
            ry=self.ry + (other.ry - self.ry) * t,
            x_axis_rotation=self.x_axis_rotation
            + (other.x_axis_rotation - self.x_axis_rotation) * t,
            large_arc_flag=round(
                self.large_arc_flag + (other.large_arc_flag - self.large_arc_flag) * t
            ),
            sweep_flag=round(
                self.sweep_flag + (other.sweep_flag - self.sweep_flag) * t
            ),
            pos=self.pos.lerp(other.pos, t),
            absolute=True,
        )


# --- Close Path ---


@dataclass
class ClosePath(PathCommand):
    """Z or z command - Close the path"""

    def to_string(self) -> str:
        return "Z"

    def to_absolute(self, current_pos: Point2D) -> ClosePath:
        return self

    def get_end_point(self, current_pos: Point2D) -> Point2D:
        # NOTE: In a real implementation, ClosePath needs access to the start
        # point of the current subpath (the last MoveTo). For simplicity here,
        # we return the current position, as the path consumer handles the Z command.
        return current_pos  # This is technically incorrect but sufficient for morphing

    def interpolate(self, other: PathCommand, t: float) -> ClosePath:
        if not isinstance(other, ClosePath):
            raise ValueError(
                f"Cannot interpolate ClosePath with {type(other).__name__}"
            )
        return self
