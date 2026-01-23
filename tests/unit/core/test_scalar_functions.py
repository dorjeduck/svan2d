"""Tests for svan2d.core.scalar_functions module."""

import math

import pytest

from svan2d.core.scalar_functions import angle, circular_midpoint, inbetween, lerp, step


@pytest.mark.unit
class TestLerp:
    """Tests for lerp function."""

    def test_lerp_at_zero(self):
        assert lerp(0, 100, 0) == 0

    def test_lerp_at_one(self):
        assert lerp(0, 100, 1) == 100

    def test_lerp_at_half(self):
        assert lerp(0, 100, 0.5) == 50.0

    def test_lerp_at_quarter(self):
        assert lerp(0, 100, 0.25) == 25.0

    def test_lerp_negative_start(self):
        assert lerp(-100, 100, 0.5) == 0.0

    def test_lerp_negative_end(self):
        assert lerp(100, -100, 0.5) == 0.0

    def test_lerp_both_negative(self):
        assert lerp(-100, -200, 0.5) == -150.0

    def test_lerp_same_values(self):
        assert lerp(50, 50, 0.7) == 50.0

    def test_lerp_with_floats(self):
        result = lerp(1.5, 3.5, 0.5)
        assert result == pytest.approx(2.5)

    def test_lerp_extrapolation_above(self):
        # t > 1 extrapolates beyond end
        assert lerp(0, 100, 1.5) == 150.0

    def test_lerp_extrapolation_below(self):
        # t < 0 extrapolates before start
        assert lerp(0, 100, -0.5) == -50.0


@pytest.mark.unit
class TestAngle:
    """Tests for angle interpolation function."""

    def test_angle_at_zero(self):
        assert angle(0, 90, 0) == 0

    def test_angle_at_one(self):
        assert angle(0, 90, 1) == 90

    def test_angle_at_half(self):
        assert angle(0, 90, 0.5) == 45

    def test_angle_shortest_path_forward(self):
        # 350 to 10 should go through 0, not 180
        result = angle(350, 10, 0.5)
        # Result should be 0 or 360 (mathematically equivalent)
        assert result == pytest.approx(0.0, abs=0.1) or result == pytest.approx(360.0, abs=0.1)

    def test_angle_shortest_path_backward(self):
        # 10 to 350 should go through 0, not 180
        result = angle(10, 350, 0.5)
        assert result == pytest.approx(0.0, abs=0.1)

    def test_angle_with_none_start(self):
        assert angle(None, 90, 1) == 90

    def test_angle_with_none_end(self):
        result = angle(90, None, 0)
        assert result == 90

    def test_angle_both_none(self):
        assert angle(None, None, 0.5) == 0

    def test_angle_wraparound_270_to_90(self):
        # 270 to 90 is 180 degrees either way
        # The function should take shortest path
        result = angle(270, 90, 0.5)
        # Could go through 0 or 180
        assert 0 <= result <= 360

    def test_angle_same_values(self):
        assert angle(45, 45, 0.5) == 45

    def test_angle_negative_normalization(self):
        # Negative angles should be normalized
        result = angle(-90, 90, 0.5)
        assert 0 <= result <= 360 or result == 0


@pytest.mark.unit
class TestStep:
    """Tests for step interpolation function."""

    def test_step_before_midpoint(self):
        assert step("hello", "world", 0.0) == "hello"
        assert step("hello", "world", 0.25) == "hello"
        assert step("hello", "world", 0.49) == "hello"

    def test_step_at_midpoint(self):
        assert step("hello", "world", 0.5) == "world"

    def test_step_after_midpoint(self):
        assert step("hello", "world", 0.75) == "world"
        assert step("hello", "world", 1.0) == "world"

    def test_step_with_bool(self):
        assert step(True, False, 0.3) == True
        assert step(True, False, 0.5) == False

    def test_step_with_int(self):
        assert step(10, 20, 0.3) == 10
        assert step(10, 20, 0.6) == 20

    def test_step_with_none(self):
        assert step(None, "value", 0.3) is None
        assert step(None, "value", 0.6) == "value"

    def test_step_with_list(self):
        list1 = [1, 2, 3]
        list2 = [4, 5, 6]
        assert step(list1, list2, 0.3) == list1
        assert step(list1, list2, 0.6) == list2


@pytest.mark.unit
class TestInbetween:
    """Tests for inbetween function."""

    def test_inbetween_single_value(self):
        result = inbetween(0, 10, 1)
        assert result == [5.0]

    def test_inbetween_four_values(self):
        result = inbetween(0, 10, 4)
        assert result == [2.0, 4.0, 6.0, 8.0]

    def test_inbetween_three_values(self):
        result = inbetween(0, 1, 3)
        assert result == [0.25, 0.5, 0.75]

    def test_inbetween_zero_values(self):
        result = inbetween(0, 10, 0)
        assert result == []

    def test_inbetween_negative_num_raises(self):
        with pytest.raises(ValueError) as exc_info:
            inbetween(0, 10, -1)
        assert "non-negative" in str(exc_info.value)

    def test_inbetween_with_floats(self):
        result = inbetween(0.0, 1.0, 1)
        assert result == [0.5]

    def test_inbetween_with_negative_range(self):
        result = inbetween(-10, 10, 1)
        assert result == [0.0]

    def test_inbetween_reversed_range(self):
        result = inbetween(10, 0, 1)
        assert result == [5.0]


@pytest.mark.unit
class TestCircularMidpoint:
    """Tests for circular_midpoint function."""

    def test_midpoint_simple(self):
        result = circular_midpoint(0, 90)
        assert result == pytest.approx(45.0, abs=0.1)

    def test_midpoint_spanning_zero(self):
        # 350 and 10 should have midpoint at 0 or 360 (equivalent)
        result = circular_midpoint(350, 10)
        assert result == pytest.approx(0.0, abs=0.1) or result == pytest.approx(360.0, abs=0.1)

    def test_midpoint_opposite_sides(self):
        # 0 and 180 should have midpoint at 90 or 270
        result = circular_midpoint(0, 180)
        assert result == pytest.approx(90.0, abs=0.1)

    def test_midpoint_same_angle(self):
        result = circular_midpoint(45, 45)
        assert result == pytest.approx(45.0, abs=0.1)

    def test_midpoint_270_90(self):
        # 270 and 90 are opposite, midpoint could be 0 or 180
        result = circular_midpoint(270, 90)
        assert result == pytest.approx(0.0, abs=0.1) or result == pytest.approx(180.0, abs=0.1)

    def test_midpoint_full_rotation(self):
        result = circular_midpoint(0, 360)
        # 0 and 360 are the same angle, midpoint could be 0, 180, or 360
        assert 0 <= result <= 360

    def test_midpoint_normalized(self):
        # Result should always be in 0-360 range
        result = circular_midpoint(350, 20)
        assert 0 <= result < 360
