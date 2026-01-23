"""Tests for svan2d.converter module."""

from unittest.mock import MagicMock, patch

import pytest

from svan2d.converter.converter_type import ConverterType
from svan2d.converter.svg_converter import SVGConverter


@pytest.fixture
def mock_scene():
    """Create a mock VScene."""
    scene = MagicMock()
    scene.width = 800
    scene.height = 600
    scene.to_svg.return_value = "<svg></svg>"
    return scene


@pytest.mark.unit
class TestConverterType:
    """Tests for ConverterType enum."""

    def test_playwright_http_value(self):
        assert ConverterType.PLAYWRIGHT_HTTP == "playwright_http"

    def test_playwright_value(self):
        assert ConverterType.PLAYWRIGHT == "playwright"

    def test_cairosvg_value(self):
        assert ConverterType.CAIROSVG == "cairosvg"

    def test_inkscape_value(self):
        assert ConverterType.INKSCAPE == "inkscape"

    def test_imagemagick_value(self):
        assert ConverterType.IMAGEMAGICK == "imagemagick"

    def test_is_string_enum(self):
        # ConverterType should be usable as a string
        assert str(ConverterType.PLAYWRIGHT) == "playwright"

    def test_all_types_exist(self):
        types = list(ConverterType)
        assert len(types) >= 4


@pytest.mark.unit
class TestSVGConverterBase:
    """Tests for SVGConverter base class helpers."""

    def test_infer_dimensions_both_none(self, mock_scene):
        """When both dimensions are None, use scene dimensions."""

        class TestConverter(SVGConverter):
            def _convert_to_png(self, *args, **kwargs):
                return {"success": True, "output": "test.png"}

            def _convert_to_pdf(self, *args, **kwargs):
                return {"success": True, "output": "test.pdf"}

        converter = TestConverter()
        width, height = converter._infer_dimensions(mock_scene, None, None)
        assert width == 800
        assert height == 600

    def test_infer_dimensions_width_only(self, mock_scene):
        """When only width given, infer height from aspect ratio."""

        class TestConverter(SVGConverter):
            def _convert_to_png(self, *args, **kwargs):
                return {"success": True, "output": "test.png"}

            def _convert_to_pdf(self, *args, **kwargs):
                return {"success": True, "output": "test.pdf"}

        converter = TestConverter()
        width, height = converter._infer_dimensions(mock_scene, 400, None)
        assert width == 400
        assert height == 300  # 400 * (600/800)

    def test_infer_dimensions_height_only(self, mock_scene):
        """When only height given, infer width from aspect ratio."""

        class TestConverter(SVGConverter):
            def _convert_to_png(self, *args, **kwargs):
                return {"success": True, "output": "test.png"}

            def _convert_to_pdf(self, *args, **kwargs):
                return {"success": True, "output": "test.pdf"}

        converter = TestConverter()
        width, height = converter._infer_dimensions(mock_scene, None, 300)
        assert width == 400  # 300 * (800/600)
        assert height == 300

    def test_infer_dimensions_both_given(self, mock_scene):
        """When both given, use as-is."""

        class TestConverter(SVGConverter):
            def _convert_to_png(self, *args, **kwargs):
                return {"success": True, "output": "test.png"}

            def _convert_to_pdf(self, *args, **kwargs):
                return {"success": True, "output": "test.pdf"}

        converter = TestConverter()
        width, height = converter._infer_dimensions(mock_scene, 1000, 500)
        assert width == 1000
        assert height == 500

    def test_svg_html_wrapping(self, mock_scene):
        """Test SVG to HTML wrapping."""

        class TestConverter(SVGConverter):
            def _convert_to_png(self, *args, **kwargs):
                return {"success": True, "output": "test.png"}

            def _convert_to_pdf(self, *args, **kwargs):
                return {"success": True, "output": "test.pdf"}

        converter = TestConverter()
        svg_content = "<svg>test</svg>"
        html = converter.svg_html(svg_content)

        assert "<!DOCTYPE html>" in html
        assert "<svg>test</svg>" in html
        assert "text-rendering: geometricPrecision" in html


@pytest.mark.unit
class TestSVGConverterConvert:
    """Tests for SVGConverter.convert method."""

    def test_convert_infers_png_from_extension(self, mock_scene):
        """When output ends in .png and no formats given, use png."""

        class TestConverter(SVGConverter):
            def _convert_to_png(self, *args, **kwargs):
                return {"success": True, "output": "test.png"}

            def _convert_to_pdf(self, *args, **kwargs):
                return {"success": True, "output": "test.pdf"}

        converter = TestConverter()
        with patch.object(converter, '_convert') as mock_convert:
            mock_convert.return_value = {"png": "test.png"}
            converter.convert(mock_scene, "output.png")
            # Should have called _convert with png format
            call_args = mock_convert.call_args
            assert "png" in call_args[0][3]  # formats argument

    def test_convert_infers_pdf_from_extension(self, mock_scene):
        """When output ends in .pdf and no formats given, use pdf."""

        class TestConverter(SVGConverter):
            def _convert_to_png(self, *args, **kwargs):
                return {"success": True, "output": "test.png"}

            def _convert_to_pdf(self, *args, **kwargs):
                return {"success": True, "output": "test.pdf"}

        converter = TestConverter()
        with patch.object(converter, '_convert') as mock_convert:
            mock_convert.return_value = {"pdf": "test.pdf"}
            converter.convert(mock_scene, "output.pdf")
            call_args = mock_convert.call_args
            assert "pdf" in call_args[0][3]

    def test_convert_uses_explicit_formats(self, mock_scene):
        """When formats given, use those."""

        class TestConverter(SVGConverter):
            def _convert_to_png(self, *args, **kwargs):
                return {"success": True, "output": "test.png"}

            def _convert_to_pdf(self, *args, **kwargs):
                return {"success": True, "output": "test.pdf"}

        converter = TestConverter()
        with patch.object(converter, '_convert') as mock_convert:
            mock_convert.return_value = {"png": "test.png", "pdf": "test.pdf"}
            converter.convert(mock_scene, "output.svg", formats=["png", "pdf"])
            call_args = mock_convert.call_args
            formats = call_args[0][3]
            assert "png" in formats
            assert "pdf" in formats


@pytest.mark.unit
class TestSVGConverterGetWriteScaledContent:
    """Tests for scaled SVG content generation."""

    def test_get_write_scaled_svg_uses_min_scale(self, mock_scene):
        """Should use min scale to fit content within bounds."""

        class TestConverter(SVGConverter):
            def _convert_to_png(self, *args, **kwargs):
                return {"success": True, "output": "test.png"}

            def _convert_to_pdf(self, *args, **kwargs):
                return {"success": True, "output": "test.pdf"}

        converter = TestConverter()
        converter._get_write_scaled_svg_content(
            mock_scene,
            frame_time=0.0,
            width=400,
            height=400
        )

        mock_scene.to_svg.assert_called_once()
        call_kwargs = mock_scene.to_svg.call_args[1]
        # For 800x600 scene -> 400x400 target, scale should be 0.5 (min of 0.5, 0.667)
        assert call_kwargs["render_scale"] == pytest.approx(0.5)


@pytest.mark.unit
class TestConcreteConverters:
    """Tests for concrete converter implementations."""

    def test_cairosvg_converter_exists(self):
        """CairoSvgConverter should be importable."""
        pytest.importorskip("cairosvg")
        from svan2d.converter.cairo_svg_converter import CairoSvgConverter
        assert CairoSvgConverter is not None

    def test_inkscape_converter_exists(self):
        """InkscapeSvgConverter should be importable."""
        from svan2d.converter.inkscape_svg_converter import InkscapeSvgConverter
        assert InkscapeSvgConverter is not None

    def test_playwright_converter_exists(self):
        """PlaywrightSvgConverter should be importable."""
        pytest.importorskip("playwright")
        from svan2d.converter.playwright_svg_converter import PlaywrightSvgConverter
        assert PlaywrightSvgConverter is not None

    def test_playwright_http_converter_exists(self):
        """PlaywrightHttpSvgConverter should be importable."""
        pytest.importorskip("requests")
        from svan2d.converter.playwright_http_svg_converter import (
            PlaywrightHttpSvgConverter,
        )
        assert PlaywrightHttpSvgConverter is not None
