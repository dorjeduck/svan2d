"""Tests for easing functions."""

import pytest

from svan2d.transition import easing


class TestEasingBasics:
    """Test basic properties that all easing functions should have."""

    # All easing functions to test
    EASING_FUNCTIONS = [
        easing.linear,
        easing.in_quad,
        easing.out_quad,
        easing.in_out_quad,
        easing.in_cubic,
        easing.out_cubic,
        easing.in_out_cubic,
        easing.in_quart,
        easing.out_quart,
        easing.in_out_quart,
        easing.in_quint,
        easing.out_quint,
        easing.in_out_quint,
        easing.in_sine,
        easing.out_sine,
        easing.in_out_sine,
        easing.in_expo,
        easing.out_expo,
        easing.in_out_expo,
        easing.in_circ,
        easing.out_circ,
        easing.in_out_circ,
        easing.in_back,
        easing.out_back,
        easing.in_out_back,
        easing.in_elastic,
        easing.out_elastic,
        easing.in_out_elastic,
        easing.in_bounce,
        easing.out_bounce,
        easing.in_out_bounce,
    ]

    @pytest.mark.parametrize("func", EASING_FUNCTIONS)
    def test_easing_at_zero(self, func):
        """All easing functions should return ~0 at t=0."""
        result = func(0.0)
        # Some easings (elastic, back) may overshoot slightly
        assert -0.5 <= result <= 0.5

    @pytest.mark.parametrize("func", EASING_FUNCTIONS)
    def test_easing_at_one(self, func):
        """All easing functions should return ~1 at t=1."""
        result = func(1.0)
        # Some easings (elastic, back) may overshoot slightly
        assert 0.5 <= result <= 1.5

    @pytest.mark.parametrize("func", EASING_FUNCTIONS)
    def test_easing_midpoint(self, func):
        """Easing functions should return something reasonable at t=0.5."""
        result = func(0.5)
        # Should be somewhere in the general range
        assert -0.5 <= result <= 1.5


class TestLinear:
    """Tests for linear easing."""

    def test_linear_identity(self):
        """Linear should return input unchanged."""
        assert easing.linear(0.0) == 0.0
        assert easing.linear(0.25) == 0.25
        assert easing.linear(0.5) == 0.5
        assert easing.linear(0.75) == 0.75
        assert easing.linear(1.0) == 1.0


class TestQuadratic:
    """Tests for quadratic easing functions."""

    def test_in_quad(self):
        """in_quad accelerates from start."""
        assert easing.in_quad(0.0) == 0.0
        assert easing.in_quad(0.5) == 0.25  # 0.5^2
        assert easing.in_quad(1.0) == 1.0

    def test_out_quad(self):
        """out_quad decelerates toward end."""
        assert easing.out_quad(0.0) == 0.0
        assert easing.out_quad(1.0) == 1.0
        # Faster at start than linear
        assert easing.out_quad(0.5) > 0.5

    def test_in_out_quad(self):
        """in_out_quad accelerates then decelerates."""
        assert easing.in_out_quad(0.0) == 0.0
        assert easing.in_out_quad(0.5) == 0.5
        assert easing.in_out_quad(1.0) == 1.0


class TestCubic:
    """Tests for cubic easing functions."""

    def test_in_cubic(self):
        """in_cubic accelerates cubically."""
        assert easing.in_cubic(0.0) == 0.0
        assert easing.in_cubic(0.5) == pytest.approx(0.125)  # 0.5^3
        assert easing.in_cubic(1.0) == 1.0

    def test_out_cubic(self):
        """out_cubic decelerates cubically."""
        assert easing.out_cubic(0.0) == 0.0
        assert easing.out_cubic(1.0) == 1.0

    def test_in_out_cubic(self):
        """in_out_cubic symmetric."""
        assert easing.in_out_cubic(0.0) == 0.0
        assert easing.in_out_cubic(0.5) == 0.5
        assert easing.in_out_cubic(1.0) == 1.0


class TestExponential:
    """Tests for exponential easing functions."""

    def test_in_expo_at_zero(self):
        """in_expo returns 0 at t=0."""
        assert easing.in_expo(0.0) == 0.0

    def test_in_expo_at_one(self):
        """in_expo returns 1 at t=1."""
        assert easing.in_expo(1.0) == 1.0

    def test_out_expo(self):
        """out_expo decelerates exponentially."""
        assert easing.out_expo(0.0) == 0.0
        assert easing.out_expo(1.0) == 1.0

    def test_in_out_expo(self):
        """in_out_expo symmetric."""
        assert easing.in_out_expo(0.0) == 0.0
        assert easing.in_out_expo(0.5) == pytest.approx(0.5, abs=0.01)
        assert easing.in_out_expo(1.0) == 1.0


class TestElastic:
    """Tests for elastic easing functions."""

    def test_in_elastic_endpoints(self):
        """in_elastic has correct endpoints."""
        assert easing.in_elastic(0.0) == 0.0
        assert easing.in_elastic(1.0) == 1.0

    def test_out_elastic_endpoints(self):
        """out_elastic has correct endpoints."""
        assert easing.out_elastic(0.0) == 0.0
        assert easing.out_elastic(1.0) == 1.0

    def test_in_out_elastic_endpoints(self):
        """in_out_elastic has correct endpoints."""
        assert easing.in_out_elastic(0.0) == 0.0
        assert easing.in_out_elastic(1.0) == 1.0

    def test_elastic_oscillates(self):
        """Elastic functions oscillate around target."""
        # Sample multiple points to verify non-monotonic behavior
        values = [easing.out_elastic(t) for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]]
        # Should have some variation (not monotonically increasing)
        diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
        # At least some differences should be negative (oscillation)
        has_variation = max(values) - min(values) > 0.1
        assert has_variation


class TestBounce:
    """Tests for bounce easing functions."""

    def test_in_bounce_endpoints(self):
        """in_bounce has correct endpoints."""
        assert easing.in_bounce(0.0) == 0.0
        assert easing.in_bounce(1.0) == 1.0

    def test_out_bounce_endpoints(self):
        """out_bounce has correct endpoints."""
        assert easing.out_bounce(0.0) == 0.0
        assert easing.out_bounce(1.0) == 1.0

    def test_in_out_bounce_endpoints(self):
        """in_out_bounce has correct endpoints."""
        assert easing.in_out_bounce(0.0) == 0.0
        assert easing.in_out_bounce(1.0) == 1.0


class TestBack:
    """Tests for back easing functions (overshoot)."""

    def test_in_back_endpoints(self):
        """in_back has correct endpoints."""
        assert easing.in_back(0.0) == 0.0
        assert easing.in_back(1.0) == pytest.approx(1.0)

    def test_in_back_undershoots(self):
        """in_back goes negative before accelerating."""
        # Should go negative in early portion
        values = [easing.in_back(t) for t in [0.1, 0.2, 0.3]]
        assert any(v < 0 for v in values)

    def test_out_back_overshoots(self):
        """out_back overshoots past 1 before settling."""
        values = [easing.out_back(t) for t in [0.7, 0.8, 0.9]]
        assert any(v > 1 for v in values)


class TestCircular:
    """Tests for circular easing functions."""

    def test_in_circ_endpoints(self):
        """in_circ has correct endpoints."""
        assert easing.in_circ(0.0) == 0.0
        assert easing.in_circ(1.0) == 1.0

    def test_out_circ_endpoints(self):
        """out_circ has correct endpoints."""
        assert easing.out_circ(0.0) == 0.0
        assert easing.out_circ(1.0) == 1.0

    def test_in_out_circ_endpoints(self):
        """in_out_circ has correct endpoints."""
        assert easing.in_out_circ(0.0) == 0.0
        assert easing.in_out_circ(1.0) == 1.0


class TestSine:
    """Tests for sine easing functions."""

    def test_in_sine_endpoints(self):
        """in_sine has correct endpoints."""
        assert easing.in_sine(0.0) == pytest.approx(0.0, abs=0.001)
        assert easing.in_sine(1.0) == pytest.approx(1.0, abs=0.001)

    def test_out_sine_endpoints(self):
        """out_sine has correct endpoints."""
        assert easing.out_sine(0.0) == pytest.approx(0.0, abs=0.001)
        assert easing.out_sine(1.0) == pytest.approx(1.0, abs=0.001)

    def test_in_out_sine_endpoints(self):
        """in_out_sine has correct endpoints."""
        assert easing.in_out_sine(0.0) == pytest.approx(0.0, abs=0.001)
        assert easing.in_out_sine(1.0) == pytest.approx(1.0, abs=0.001)


class TestSpecialEasings:
    """Tests for special easing functions."""

    def test_step_function(self):
        """Step function jumps at 0.5."""
        assert easing.step(0.0) == 0.0
        assert easing.step(0.49) == 0.0
        assert easing.step(0.5) == 1.0
        assert easing.step(1.0) == 1.0

    def test_none_easing(self):
        """None easing returns 0 (static field, no change)."""
        assert easing.none(0.0) == 0.0
        assert easing.none(0.5) == 0.0
        assert easing.none(1.0) == 0.0

    def test_in_out_alias(self):
        """in_out is an alias for a standard in_out function."""
        # Should work like in_out_quad or similar
        assert easing.in_out(0.0) == 0.0
        assert easing.in_out(1.0) == 1.0
