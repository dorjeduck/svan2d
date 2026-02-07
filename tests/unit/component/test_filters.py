"""Tests for filter effects."""

import pytest

from svan2d.component.effect.filter import (
    GaussianBlurFilter,
    DropShadowFilter,
    MorphologyFilter,
    OffsetFilter,
)


class TestGaussianBlurFilter:
    """Tests for GaussianBlurFilter."""

    def test_creation_default(self):
        """Create with default values."""
        blur = GaussianBlurFilter()
        assert blur.std_deviation == 0.0
        assert blur.std_deviation_x is None
        assert blur.std_deviation_y is None

    def test_creation_with_deviation(self):
        """Create with standard deviation."""
        blur = GaussianBlurFilter(std_deviation=5.0)
        assert blur.std_deviation == 5.0

    def test_creation_with_separate_xy(self):
        """Create with separate x/y deviations."""
        blur = GaussianBlurFilter(std_deviation_x=10.0, std_deviation_y=2.0)
        assert blur.std_deviation_x == 10.0
        assert blur.std_deviation_y == 2.0

    def test_negative_deviation_raises(self):
        """Negative std_deviation raises ValueError."""
        with pytest.raises(ValueError, match="must be >= 0"):
            GaussianBlurFilter(std_deviation=-1.0)

    def test_negative_deviation_x_raises(self):
        """Negative std_deviation_x raises ValueError."""
        with pytest.raises(ValueError, match="must be >= 0"):
            GaussianBlurFilter(std_deviation_x=-1.0)

    def test_negative_deviation_y_raises(self):
        """Negative std_deviation_y raises ValueError."""
        with pytest.raises(ValueError, match="must be >= 0"):
            GaussianBlurFilter(std_deviation_y=-1.0)

    def test_to_drawsvg(self):
        """Convert to drawsvg FilterItem."""
        blur = GaussianBlurFilter(std_deviation=5.0)
        result = blur.to_drawsvg()
        assert result is not None

    def test_to_drawsvg_separate_xy(self):
        """Convert with separate x/y to drawsvg."""
        blur = GaussianBlurFilter(std_deviation_x=10.0, std_deviation_y=2.0)
        result = blur.to_drawsvg()
        assert result is not None

    def test_interpolate_same_type(self):
        """Interpolate between two GaussianBlurFilters."""
        blur1 = GaussianBlurFilter(std_deviation=0.0)
        blur2 = GaussianBlurFilter(std_deviation=10.0)

        result = blur1.interpolate(blur2, 0.5)
        assert isinstance(result, GaussianBlurFilter)
        assert result.std_deviation == pytest.approx(5.0)

    def test_interpolate_at_zero(self):
        """Interpolate at t=0 returns start value."""
        blur1 = GaussianBlurFilter(std_deviation=2.0)
        blur2 = GaussianBlurFilter(std_deviation=10.0)

        result = blur1.interpolate(blur2, 0.0)
        assert result.std_deviation == pytest.approx(2.0)

    def test_interpolate_at_one(self):
        """Interpolate at t=1 returns end value."""
        blur1 = GaussianBlurFilter(std_deviation=2.0)
        blur2 = GaussianBlurFilter(std_deviation=10.0)

        result = blur1.interpolate(blur2, 1.0)
        assert result.std_deviation == pytest.approx(10.0)

    def test_interpolate_with_xy(self):
        """Interpolate with separate x/y deviations."""
        blur1 = GaussianBlurFilter(std_deviation_x=0.0, std_deviation_y=0.0)
        blur2 = GaussianBlurFilter(std_deviation_x=10.0, std_deviation_y=20.0)

        result = blur1.interpolate(blur2, 0.5)
        assert result.std_deviation_x == pytest.approx(5.0)
        assert result.std_deviation_y == pytest.approx(10.0)


class TestDropShadowFilter:
    """Tests for DropShadowFilter."""

    def test_creation_default(self):
        """Create with default values."""
        shadow = DropShadowFilter()
        assert shadow.dx == 2.0
        assert shadow.dy == 2.0
        assert shadow.std_deviation == 2.0

    def test_creation_custom(self):
        """Create with custom values."""
        shadow = DropShadowFilter(dx=5.0, dy=5.0, std_deviation=3.0)
        assert shadow.dx == 5.0
        assert shadow.dy == 5.0
        assert shadow.std_deviation == 3.0

    def test_to_drawsvg(self):
        """Convert to drawsvg FilterItem."""
        shadow = DropShadowFilter(dx=3.0, dy=3.0, std_deviation=2.0)
        result = shadow.to_drawsvg()
        assert result is not None


class TestMorphologyFilter:
    """Tests for MorphologyFilter."""

    def test_creation_dilate(self):
        """Create dilate morphology filter."""
        morph = MorphologyFilter(operator="dilate", radius=2.0)
        assert morph.operator == "dilate"
        assert morph.radius == 2.0

    def test_creation_erode(self):
        """Create erode morphology filter."""
        morph = MorphologyFilter(operator="erode", radius=1.0)
        assert morph.operator == "erode"
        assert morph.radius == 1.0

    def test_to_drawsvg(self):
        """Convert to drawsvg FilterItem."""
        morph = MorphologyFilter(operator="dilate", radius=2.0)
        result = morph.to_drawsvg()
        assert result is not None


class TestOffsetFilter:
    """Tests for OffsetFilter."""

    def test_creation_default(self):
        """Create with default values."""
        offset = OffsetFilter()
        assert offset.dx == 0.0
        assert offset.dy == 0.0

    def test_creation_custom(self):
        """Create with custom offset."""
        offset = OffsetFilter(dx=10.0, dy=20.0)
        assert offset.dx == 10.0
        assert offset.dy == 20.0

    def test_to_drawsvg(self):
        """Convert to drawsvg FilterItem."""
        offset = OffsetFilter(dx=5.0, dy=5.0)
        result = offset.to_drawsvg()
        assert result is not None
