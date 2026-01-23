"""Tests for svan2d.core.point2d module."""

import math

import pytest

from svan2d.core.point2d import Point2D, Points2D, _lerp
from svan2d.core.mutable_point2d import (
    MutablePoint2D,
    MutablePoint2DPool,
    get_pooled_point,
    reset_point_pool,
)


@pytest.mark.unit
class TestPoint2DCreation:
    """Tests for Point2D initialization."""

    def test_default_values(self):
        p = Point2D()
        assert p.x == 0
        assert p.y == 0

    def test_create_with_values(self):
        p = Point2D(10.0, 20.0)
        assert p.x == 10.0
        assert p.y == 20.0

    def test_create_with_negative_values(self):
        p = Point2D(-5.5, -10.5)
        assert p.x == -5.5
        assert p.y == -10.5

    def test_point2d_is_frozen(self):
        p = Point2D(10, 20)
        with pytest.raises(AttributeError):
            p.x = 30


@pytest.mark.unit
class TestPoint2DUnpacking:
    """Tests for Point2D iteration/unpacking."""

    def test_unpack_to_xy(self):
        p = Point2D(10.0, 20.0)
        x, y = p
        assert x == 10.0
        assert y == 20.0

    def test_iterate(self):
        p = Point2D(10.0, 20.0)
        values = list(p)
        assert values == [10.0, 20.0]


@pytest.mark.unit
class TestPoint2DOperations:
    """Tests for Point2D arithmetic operations."""

    def test_add(self):
        p1 = Point2D(10, 20)
        p2 = Point2D(5, 10)
        result = p1 + p2
        assert result.x == 15
        assert result.y == 30

    def test_sub(self):
        p1 = Point2D(10, 20)
        p2 = Point2D(5, 10)
        result = p1 - p2
        assert result.x == 5
        assert result.y == 10

    def test_mul_scalar(self):
        p = Point2D(10, 20)
        result = p * 2
        assert result.x == 20
        assert result.y == 40

    def test_rmul_scalar(self):
        p = Point2D(10, 20)
        result = 2 * p
        assert result.x == 20
        assert result.y == 40

    def test_truediv_scalar(self):
        p = Point2D(20, 40)
        result = p / 2
        assert result.x == 10
        assert result.y == 20

    def test_truediv_by_zero_raises(self):
        p = Point2D(10, 20)
        with pytest.raises(ZeroDivisionError):
            p / 0

    def test_neg(self):
        p = Point2D(10, -20)
        result = -p
        assert result.x == -10
        assert result.y == 20


@pytest.mark.unit
class TestPoint2DGeometry:
    """Tests for Point2D geometric operations."""

    def test_distance_to_same_point(self):
        p1 = Point2D(10, 20)
        p2 = Point2D(10, 20)
        assert p1.distance_to(p2) == 0.0

    def test_distance_to_horizontal(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(10, 0)
        assert p1.distance_to(p2) == 10.0

    def test_distance_to_vertical(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(0, 10)
        assert p1.distance_to(p2) == 10.0

    def test_distance_to_diagonal(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(3, 4)
        assert p1.distance_to(p2) == 5.0

    def test_center_to(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(10, 10)
        center = p1.center_to(p2)
        assert center.x == 5.0
        assert center.y == 5.0

    def test_rotation_to_right(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(10, 0)
        angle = p1.rotation_to(p2)
        assert angle == pytest.approx(0.0, abs=0.1)

    def test_rotation_to_up(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(0, 10)
        angle = p1.rotation_to(p2)
        assert angle == pytest.approx(90.0, abs=0.1)

    def test_rotation_to_left(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(-10, 0)
        angle = p1.rotation_to(p2)
        assert angle == pytest.approx(180.0, abs=0.1)

    def test_rotation_to_down(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(0, -10)
        angle = p1.rotation_to(p2)
        assert angle == pytest.approx(-90.0, abs=0.1)


@pytest.mark.unit
class TestPoint2DWithMethods:
    """Tests for Point2D with_x/with_y methods."""

    def test_with_x(self):
        p = Point2D(10, 20)
        result = p.with_x(50)
        assert result.x == 50
        assert result.y == 20

    def test_with_y(self):
        p = Point2D(10, 20)
        result = p.with_y(50)
        assert result.x == 10
        assert result.y == 50


@pytest.mark.unit
class TestPoint2DLerp:
    """Tests for Point2D linear interpolation."""

    def test_lerp_start(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(10, 20)
        result = p1.lerp(p2, 0.0)
        assert result.x == 0.0
        assert result.y == 0.0

    def test_lerp_end(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(10, 20)
        result = p1.lerp(p2, 1.0)
        assert result.x == 10.0
        assert result.y == 20.0

    def test_lerp_midpoint(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(10, 20)
        result = p1.lerp(p2, 0.5)
        assert result.x == 5.0
        assert result.y == 10.0

    def test_lerp_quarter(self):
        p1 = Point2D(0, 0)
        p2 = Point2D(100, 200)
        result = p1.lerp(p2, 0.25)
        assert result.x == 25.0
        assert result.y == 50.0


@pytest.mark.unit
class TestPoint2DEquality:
    """Tests for Point2D equality and hashing."""

    def test_equal_points(self):
        p1 = Point2D(10, 20)
        p2 = Point2D(10, 20)
        assert p1 == p2

    def test_unequal_points(self):
        p1 = Point2D(10, 20)
        p2 = Point2D(10, 21)
        assert p1 != p2

    def test_hash_for_dict(self):
        p1 = Point2D(10, 20)
        p2 = Point2D(10, 20)
        d = {p1: "point"}
        assert d[p2] == "point"

    def test_hash_for_set(self):
        p1 = Point2D(10, 20)
        p2 = Point2D(10, 20)
        s = {p1}
        assert p2 in s


@pytest.mark.unit
class TestPoints2DType:
    """Tests for Points2D type alias."""

    def test_points2d_is_list(self):
        points: Points2D = [Point2D(0, 0), Point2D(10, 10)]
        assert isinstance(points, list)
        assert len(points) == 2
        assert all(isinstance(p, Point2D) for p in points)


@pytest.mark.unit
class TestMutablePoint2D:
    """Tests for MutablePoint2D."""

    def test_create_default(self):
        p = MutablePoint2D()
        assert p.x == 0.0
        assert p.y == 0.0

    def test_create_with_values(self):
        p = MutablePoint2D(10.0, 20.0)
        assert p.x == 10.0
        assert p.y == 20.0

    def test_is_mutable(self):
        p = MutablePoint2D(10, 20)
        p.x = 30
        assert p.x == 30

    def test_set_method(self):
        p = MutablePoint2D()
        result = p.set(5.0, 10.0)
        assert p.x == 5.0
        assert p.y == 10.0
        assert result is p

    def test_to_point2d(self):
        p = MutablePoint2D(10.0, 20.0)
        frozen = p.to_point2d()
        assert isinstance(frozen, Point2D)
        assert frozen.x == 10.0
        assert frozen.y == 20.0

    def test_lerp_from(self):
        p = MutablePoint2D()
        p1 = Point2D(0, 0)
        p2 = Point2D(10, 20)
        result = p.lerp_from(p1, p2, 0.5)
        assert p.x == 5.0
        assert p.y == 10.0
        assert result is p


@pytest.mark.unit
class TestMutablePoint2DPool:
    """Tests for MutablePoint2DPool object pooling."""

    def test_pool_creation(self):
        pool = MutablePoint2DPool(10)
        assert pool.capacity == 10
        assert pool.used == 0

    def test_pool_get(self):
        pool = MutablePoint2DPool(10)
        p = pool.get(5.0, 10.0)
        assert isinstance(p, MutablePoint2D)
        assert p.x == 5.0
        assert p.y == 10.0
        assert pool.used == 1

    def test_pool_reset(self):
        pool = MutablePoint2DPool(10)
        pool.get()
        pool.get()
        assert pool.used == 2
        pool.reset()
        assert pool.used == 0

    def test_pool_grows(self):
        pool = MutablePoint2DPool(2)
        for _ in range(5):
            pool.get()
        assert pool.used == 5
        assert pool.capacity >= 5

    def test_global_pool_functions(self):
        reset_point_pool()
        p = get_pooled_point(1.0, 2.0)
        assert p.x == 1.0
        assert p.y == 2.0


@pytest.mark.unit
class TestLerpFunction:
    """Tests for internal _lerp function."""

    def test_lerp_zero(self):
        assert _lerp(0, 100, 0) == 0

    def test_lerp_one(self):
        assert _lerp(0, 100, 1) == 100

    def test_lerp_half(self):
        assert _lerp(0, 100, 0.5) == 50

    def test_lerp_negative(self):
        assert _lerp(-50, 50, 0.5) == 0

    def test_lerp_extrapolation(self):
        # t outside [0, 1] extrapolates
        assert _lerp(0, 100, 1.5) == 150
        assert _lerp(0, 100, -0.5) == -50
