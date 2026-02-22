"""Tests for auto-expand of single-keystate VElements."""

import pytest

from svan2d.component.state.circle import CircleState
from svan2d.core.point2d import Point2D
from svan2d.velement import VElement


class TestAutoExpandSingleKeystate:
    """VElement(state=s) should persist across the full [0, 1] timeline."""

    def test_implicit_time_visible_at_start(self):
        """VElement(state=s) renders at t=0.0."""
        state = CircleState(radius=50, pos=Point2D(10, 20))
        element = VElement(state=state)

        frame = element.get_frame(0.0)
        assert frame is not None
        assert frame.radius == 50

    def test_implicit_time_visible_at_midpoint(self):
        """VElement(state=s) renders at t=0.5 (auto-expanded)."""
        state = CircleState(radius=50, pos=Point2D(10, 20))
        element = VElement(state=state)

        frame = element.get_frame(0.5)
        assert frame is not None
        assert frame.radius == 50
        assert frame.pos.x == pytest.approx(10)
        assert frame.pos.y == pytest.approx(20)

    def test_implicit_time_visible_at_end(self):
        """VElement(state=s) renders at t=1.0."""
        state = CircleState(radius=50)
        element = VElement(state=state)

        frame = element.get_frame(1.0)
        assert frame is not None
        assert frame.radius == 50

    def test_explicit_time_single_keystate_not_expanded(self):
        """VElement().keystate(s, at=0.0) with explicit time should NOT auto-expand."""
        state = CircleState(radius=50)
        element = VElement().keystate(state, at=0.0)

        # At t=0.0 it should render
        frame = element.get_frame(0.0)
        assert frame is not None

        # At t=0.5 it should return None (not expanded)
        frame = element.get_frame(0.5)
        assert frame is None

    def test_implicit_keystate_via_builder(self):
        """VElement().keystate(s) without at= should also auto-expand."""
        state = CircleState(radius=75)
        element = VElement().keystate(state)

        frame = element.get_frame(0.5)
        assert frame is not None
        assert frame.radius == 75
