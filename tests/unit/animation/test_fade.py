"""Tests for fade animation"""

import pytest
from svan2d.animation import fade
from svan2d.component.state.circle import CircleState
from svan2d.core.point2d import Point2D
from svan2d.velement import VElement


class TestFadeBasic:
    """Basic fade functionality tests"""

    def test_fade_returns_list_of_velements(self):
        """fade() should return list of VElements"""
        s1 = CircleState(radius=50)
        s2 = CircleState(radius=100)

        elements = fade([s1, s2])

        assert isinstance(elements, list)
        assert len(elements) == 2
        assert all(isinstance(e, VElement) for e in elements)

    def test_fade_two_states(self):
        """fade with 2 states creates 2 elements"""
        s1 = CircleState(radius=50)
        s2 = CircleState(radius=100)

        elements = fade([s1, s2])

        assert len(elements) == 2

    def test_fade_three_states(self):
        """fade with 3 states creates 3 elements"""
        s1 = CircleState(radius=50)
        s2 = CircleState(radius=75)
        s3 = CircleState(radius=100)

        elements = fade([s1, s2, s3])

        assert len(elements) == 3

    def test_fade_minimum_states_error(self):
        """fade with less than 2 states should error"""
        s1 = CircleState(radius=50)

        with pytest.raises(ValueError, match="at least 2 states"):
            fade([s1])

    def test_fade_empty_states_error(self):
        """fade with empty list should error"""
        with pytest.raises(ValueError, match="at least 2 states"):
            fade([])


class TestFadeContinuation:
    """Tests for continuation from fade elements"""

    def test_all_elements_are_velement(self):
        """All elements should be VElement"""
        s1 = CircleState(radius=50)
        s2 = CircleState(radius=100)

        elements = fade([s1, s2])

        assert all(isinstance(e, VElement) for e in elements)

    def test_continuation_from_last_element(self):
        """Should be able to continue from last element before render"""
        s1 = CircleState(radius=50)
        s2 = CircleState(radius=100)
        s3 = CircleState(radius=150)

        elements = fade([s1, s2], start=0.0, end=0.5)

        # Continue the last element (before first render)
        elements[-1].keystate(s3, at=1.0)

        # Trigger build by getting frame
        frame = elements[-1].get_frame(1.0)

        assert frame is not None
        assert len(elements[-1].keystates) >= 2


class TestFadeTiming:
    """Tests for timing parameters"""

    def test_custom_start_end(self):
        """fade should respect start/end times"""
        s1 = CircleState(radius=50)
        s2 = CircleState(radius=100)

        elements = fade([s1, s2], start=0.2, end=0.8)

        # Trigger build
        elements[0].get_frame(0.2)
        elements[-1].get_frame(0.8)

        # First element should start at 0.2
        assert elements[0].keystates[0].time == pytest.approx(0.2, rel=0.01)
        # Last element should end at 0.8
        assert elements[-1].keystates[-1].time == pytest.approx(0.8, rel=0.01)

    def test_fade_duration(self):
        """fade_duration should control fade length"""
        s1 = CircleState(radius=50)
        s2 = CircleState(radius=100)

        elements = fade([s1, s2], fade_duration=0.2)

        # Elements should exist
        assert len(elements) == 2

    def test_negative_gap_overlap(self):
        """Negative gap should create overlapping elements"""
        s1 = CircleState(radius=50)
        s2 = CircleState(radius=100)

        # With negative gap, second element starts before first ends
        elements = fade([s1, s2], gap=-0.05)

        # Both elements should exist and be valid
        assert len(elements) == 2
        assert all(isinstance(e, VElement) for e in elements)


class TestFadeOpacity:
    """Tests for opacity transitions"""

    def test_first_element_fades_out(self):
        """First element should fade from 1.0 to 0.0"""
        s1 = CircleState(radius=50)
        s2 = CircleState(radius=100)

        elements = fade([s1, s2])

        first = elements[0]
        # Trigger build
        first.get_frame(0.0)

        # First keystate should be opacity 1.0
        assert first.keystates[0].state.opacity == 1.0
        # Last keystate should be opacity 0.0
        assert first.keystates[-1].state.opacity == 0.0

    def test_last_element_fades_in(self):
        """Last element should fade from 0.0 to 1.0"""
        s1 = CircleState(radius=50)
        s2 = CircleState(radius=100)

        elements = fade([s1, s2])

        last = elements[-1]
        # Trigger build
        last.get_frame(1.0)

        # First keystate should be opacity 0.0
        assert last.keystates[0].state.opacity == 0.0
        # Should reach opacity 1.0
        assert any(ks.state.opacity == 1.0 for ks in last.keystates)
