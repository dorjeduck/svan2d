"""Tests for transition curve functions (path interpolation)."""

import pytest

from svan2d.core.point2d import Point2D
from svan2d.transition.curve.arc import arc, arc_clockwise, arc_counterclockwise
from svan2d.transition.curve.bezier import bezier, bezier_quadratic, bezier_cubic
from svan2d.transition.curve.linear import linear


class TestLinearCurve:
    """Tests for linear path interpolation."""

    def test_linear_at_zero(self):
        """Linear returns start point at t=0."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 100)
        result = linear(p1, p2, 0.0)
        assert result.x == pytest.approx(0.0)
        assert result.y == pytest.approx(0.0)

    def test_linear_at_one(self):
        """Linear returns end point at t=1."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 100)
        result = linear(p1, p2, 1.0)
        assert result.x == pytest.approx(100.0)
        assert result.y == pytest.approx(100.0)

    def test_linear_midpoint(self):
        """Linear returns midpoint at t=0.5."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 100)
        result = linear(p1, p2, 0.5)
        assert result.x == pytest.approx(50.0)
        assert result.y == pytest.approx(50.0)


class TestBezierCurve:
    """Tests for bezier path interpolation."""

    def test_bezier_quadratic_endpoints(self):
        """Quadratic bezier returns correct endpoints."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)
        cp = Point2D(50, 100)  # Control point above midpoint

        path_func = bezier([cp])

        result_start = path_func(p1, p2, 0.0)
        assert result_start.x == pytest.approx(0.0)
        assert result_start.y == pytest.approx(0.0)

        result_end = path_func(p1, p2, 1.0)
        assert result_end.x == pytest.approx(100.0)
        assert result_end.y == pytest.approx(0.0)

    def test_bezier_quadratic_midpoint(self):
        """Quadratic bezier curves toward control point."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)
        cp = Point2D(50, 100)  # Control point above

        path_func = bezier([cp])
        result = path_func(p1, p2, 0.5)

        # At t=0.5, should be at x=50 and y > 0 (curved upward)
        assert result.x == pytest.approx(50.0)
        assert result.y > 0  # Curved toward control point

    def test_bezier_cubic_endpoints(self):
        """Cubic bezier returns correct endpoints."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)
        cp1 = Point2D(25, 50)
        cp2 = Point2D(75, 50)

        path_func = bezier([cp1, cp2])

        result_start = path_func(p1, p2, 0.0)
        assert result_start.x == pytest.approx(0.0)
        assert result_start.y == pytest.approx(0.0)

        result_end = path_func(p1, p2, 1.0)
        assert result_end.x == pytest.approx(100.0)
        assert result_end.y == pytest.approx(0.0)

    def test_bezier_empty_control_points_raises(self):
        """Bezier with no control points should raise."""
        with pytest.raises(ValueError, match="at least one control point"):
            bezier([])

    def test_bezier_invalid_control_point_raises(self):
        """Bezier with invalid control point type should raise."""
        with pytest.raises(TypeError, match="Point2D objects"):
            bezier([(50, 100)])  # Tuple instead of Point2D

    def test_bezier_quadratic_convenience(self):
        """bezier_quadratic convenience function works."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)
        cp = Point2D(50, 100)

        path_func = bezier_quadratic(cp)
        result = path_func(p1, p2, 0.5)

        assert result.x == pytest.approx(50.0)
        assert result.y > 0

    def test_bezier_cubic_convenience(self):
        """bezier_cubic convenience function works."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)
        cp1 = Point2D(25, 50)
        cp2 = Point2D(75, 50)

        path_func = bezier_cubic(cp1, cp2)
        result = path_func(p1, p2, 0.5)

        assert result.x == pytest.approx(50.0)
        assert result.y > 0


class TestArcCurve:
    """Tests for arc path interpolation."""

    def test_arc_counterclockwise_endpoints(self):
        """Arc counterclockwise returns correct endpoints."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)

        path_func = arc_counterclockwise(100)

        result_start = path_func(p1, p2, 0.0)
        assert result_start.x == pytest.approx(0.0, abs=0.1)
        assert result_start.y == pytest.approx(0.0, abs=0.1)

        result_end = path_func(p1, p2, 1.0)
        assert result_end.x == pytest.approx(100.0, abs=0.1)
        assert result_end.y == pytest.approx(0.0, abs=0.1)

    def test_arc_clockwise_endpoints(self):
        """Arc clockwise returns correct endpoints."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)

        path_func = arc_clockwise(100)

        result_start = path_func(p1, p2, 0.0)
        assert result_start.x == pytest.approx(0.0, abs=0.1)
        assert result_start.y == pytest.approx(0.0, abs=0.1)

        result_end = path_func(p1, p2, 1.0)
        assert result_end.x == pytest.approx(100.0, abs=0.1)
        assert result_end.y == pytest.approx(0.0, abs=0.1)

    def test_arc_midpoint_curves_away_from_line(self):
        """Arc midpoint should be off the direct line."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)

        path_func = arc_clockwise(100)
        result = path_func(p1, p2, 0.5)

        # Midpoint should be at x~50 but y != 0 (curved)
        assert result.x == pytest.approx(50.0, abs=5)
        assert result.y != pytest.approx(0.0, abs=0.1)

    def test_arc_default_radius(self):
        """Arc with default radius (None) uses distance."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)

        path_func = arc_clockwise(None)  # Will use distance as radius
        result = path_func(p1, p2, 0.5)

        # Should still curve
        assert result.y != pytest.approx(0.0, abs=0.1)

    def test_arc_same_point(self):
        """Arc with same start and end returns start."""
        p1 = Point2D(50, 50)
        p2 = Point2D(50, 50)

        path_func = arc_clockwise(100)
        result = path_func(p1, p2, 0.5)

        assert result.x == pytest.approx(50.0)
        assert result.y == pytest.approx(50.0)

    def test_arc_small_radius_clamped(self):
        """Arc radius smaller than half distance is clamped."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)

        # Radius 10 is too small (min is 50 for distance 100)
        path_func = arc_clockwise(10)
        result = path_func(p1, p2, 0.5)

        # Should still work (clamped to minimum)
        assert 0 <= result.x <= 100

    def test_arc_alias(self):
        """arc() is alias for arc_counterclockwise()."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)

        path_func1 = arc(100)
        path_func2 = arc_counterclockwise(100)

        result1 = path_func1(p1, p2, 0.5)
        result2 = path_func2(p1, p2, 0.5)

        assert result1.x == pytest.approx(result2.x)
        assert result1.y == pytest.approx(result2.y)

    def test_arc_clockwise_vs_counterclockwise(self):
        """Clockwise and counterclockwise produce different paths."""
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 0)

        cw_func = arc_clockwise(100)
        ccw_func = arc_counterclockwise(100)

        cw_mid = cw_func(p1, p2, 0.5)
        ccw_mid = ccw_func(p1, p2, 0.5)

        # The y values should be different (different arc paths)
        assert cw_mid.y != pytest.approx(ccw_mid.y, abs=1.0)
