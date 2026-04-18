"""Tests for state bounding box computation."""

import math

import pytest

from svan2d.primitive.state.bounds import state_bounds
from svan2d.primitive.state.circle import CircleState
from svan2d.primitive.state.rectangle import RectangleState
from svan2d.primitive.state.text import TextState
from svan2d.core.point2d import Point2D


@pytest.mark.unit
class TestStateBounds:
    def test_circle_at_origin(self):
        state = CircleState(radius=50)
        bounds = state_bounds(state)
        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == pytest.approx(-50, abs=1)
        assert min_y == pytest.approx(-50, abs=1)
        assert max_x == pytest.approx(50, abs=1)
        assert max_y == pytest.approx(50, abs=1)

    def test_circle_with_pos_offset(self):
        state = CircleState(radius=30, pos=Point2D(100, 200))
        bounds = state_bounds(state)
        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == pytest.approx(70, abs=1)
        assert min_y == pytest.approx(170, abs=1)
        assert max_x == pytest.approx(130, abs=1)
        assert max_y == pytest.approx(230, abs=1)

    def test_circle_with_scale(self):
        state = CircleState(radius=50, scale=2.0)
        bounds = state_bounds(state)
        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == pytest.approx(-100, abs=2)
        assert min_y == pytest.approx(-100, abs=2)
        assert max_x == pytest.approx(100, abs=2)
        assert max_y == pytest.approx(100, abs=2)

    def test_rectangle_with_rotation(self):
        # 100x60 rectangle rotated 45 degrees
        state = RectangleState(width=100, height=60, rotation=45)
        bounds = state_bounds(state)
        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        # At 45deg, AABB width = w*cos45 + h*sin45 (same for height)
        cos45 = math.cos(math.radians(45))
        expected = (100 * cos45 + 60 * cos45)
        assert max_x - min_x == pytest.approx(expected, abs=2)
        assert max_y - min_y == pytest.approx(expected, abs=2)

    def test_text_returns_point_bounds(self):
        state = TextState(text="hello", pos=Point2D(50, 75))
        bounds = state_bounds(state)
        assert bounds is not None
        # Text falls back to point at pos
        assert bounds == pytest.approx((50, 75, 50, 75), abs=0.01)
