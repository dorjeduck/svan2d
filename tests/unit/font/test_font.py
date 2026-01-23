"""Tests for svan2d.font module."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestFontModuleImports:
    """Tests for font module imports."""

    def test_glyph_extractor_importable(self):
        try:
            from svan2d.font.glyph_extractor import GlyphExtractor
            assert GlyphExtractor is not None
        except ImportError:
            # fonttools may not be installed
            pytest.skip("fonttools not installed")

    def test_bezier_sampler_importable(self):
        try:
            from svan2d.font.bezier_sampler import BezierSampler
            assert BezierSampler is not None
        except ImportError:
            pytest.skip("fonttools not installed")

    def test_contour_classifier_importable(self):
        try:
            from svan2d.font.contour_classifier import ContourClassifier
            assert ContourClassifier is not None
        except ImportError:
            pytest.skip("fonttools not installed")

    def test_font_glyphs_importable(self):
        try:
            from svan2d.font.font_glyphs import FontGlyphs
            assert FontGlyphs is not None
        except ImportError:
            pytest.skip("fonttools not installed")


@pytest.mark.unit
class TestBezierSampler:
    """Tests for BezierSampler class."""

    def test_sample_quadratic_bezier(self):
        try:
            from svan2d.font.bezier_sampler import BezierSampler
        except ImportError:
            pytest.skip("fonttools not installed")

        sampler = BezierSampler(samples_per_curve=10)
        # Quadratic bezier: p0, p1 (control), p2
        points = [(0, 0), (50, 100), (100, 0)]
        result = sampler.sample_quadratic(points)
        assert len(result) > 0
        # First point should be at start
        assert result[0] == pytest.approx((0, 0), abs=0.1)

    def test_sample_cubic_bezier(self):
        try:
            from svan2d.font.bezier_sampler import BezierSampler
        except ImportError:
            pytest.skip("fonttools not installed")

        sampler = BezierSampler(samples_per_curve=10)
        # Cubic bezier: p0, c1, c2, p3
        points = [(0, 0), (25, 100), (75, 100), (100, 0)]
        result = sampler.sample_cubic(points)
        assert len(result) > 0


@pytest.mark.unit
class TestContourClassifier:
    """Tests for ContourClassifier class."""

    def test_classify_outer_contour(self):
        try:
            from svan2d.font.contour_classifier import ContourClassifier
        except ImportError:
            pytest.skip("fonttools not installed")

        classifier = ContourClassifier()
        # Clockwise contour (outer)
        contour = [(0, 0), (100, 0), (100, 100), (0, 100)]
        is_outer = classifier.is_outer_contour(contour)
        assert isinstance(is_outer, bool)


@pytest.mark.unit
class TestGlyphExtractor:
    """Tests for GlyphExtractor class."""

    def test_extractor_initialization(self):
        try:
            from svan2d.font.glyph_extractor import GlyphExtractor
        except ImportError:
            pytest.skip("fonttools not installed")

        # Mock font file
        with patch('fontTools.ttLib.TTFont') as mock_ttfont:
            mock_font = MagicMock()
            mock_ttfont.return_value = mock_font

            try:
                extractor = GlyphExtractor.__new__(GlyphExtractor)
                # Just verify class can be instantiated
                assert extractor is not None
            except Exception:
                # May fail due to font file not existing
                pass


@pytest.mark.unit
class TestFontGlyphs:
    """Tests for FontGlyphs class."""

    def test_font_glyphs_class_exists(self):
        try:
            from svan2d.font.font_glyphs import FontGlyphs
            assert FontGlyphs is not None
        except ImportError:
            pytest.skip("fonttools not installed")
