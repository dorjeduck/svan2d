"""Tests for svan2d.vscene.vscene_exporter module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from svan2d.converter.converter_type import ConverterType
from svan2d.vscene.vscene_exporter import ExportResult, VSceneExporter


@pytest.fixture
def mock_scene():
    """Create a mock VScene."""
    scene = MagicMock()
    scene.width = 100
    scene.height = 100
    scene.to_svg.return_value = "<svg></svg>"
    scene.to_drawing.return_value = MagicMock()
    return scene


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.mark.unit
class TestExportResultDataclass:
    """Tests for ExportResult dataclass."""

    def test_create_success_result(self):
        result = ExportResult(success=True, files={"svg": "/path/to/file.svg"})
        assert result.success is True
        assert result.files["svg"] == "/path/to/file.svg"
        assert result.error is None

    def test_create_failure_result(self):
        result = ExportResult(success=False, files={}, error="Export failed")
        assert result.success is False
        assert result.error == "Export failed"


@pytest.mark.unit
class TestVSceneExporterCreation:
    """Tests for VSceneExporter initialization."""

    def test_create_with_defaults(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            assert exporter.scene is mock_scene
            assert exporter.output_dir == Path(temp_dir)
            assert exporter.timestamp_files is False

    def test_create_with_timestamp(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(
                mock_scene, output_dir=temp_dir, timestamp_files=True
            )
            assert exporter.timestamp_files is True


@pytest.mark.unit
class TestVSceneExporterValidation:
    """Tests for validation methods."""

    def test_validate_formats_valid(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            exporter._validate_formats(["svg", "png", "pdf"])  # Should not raise

    def test_validate_formats_invalid(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            with pytest.raises(ValueError) as exc_info:
                exporter._validate_formats(["svg", "mp3"])
            assert "mp3" in str(exc_info.value)

    def test_validate_video_params_valid(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            exporter._validate_video_params(60, 30, 5, "libx264")  # Should not raise

    def test_validate_video_params_invalid_frames(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            with pytest.raises(ValueError):
                exporter._validate_video_params(0, 30, 5, "libx264")

    def test_validate_video_params_invalid_framerate(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            with pytest.raises(ValueError):
                exporter._validate_video_params(60, 0, 5, "libx264")

    def test_validate_dimensions_valid(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            exporter._validate_dimensions(100, 100, 8.5, 11.0)  # Should not raise

    def test_validate_dimensions_invalid_png(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            with pytest.raises(ValueError):
                exporter._validate_dimensions(0, None, None, None)


@pytest.mark.unit
class TestVSceneExporterHelpers:
    """Tests for helper methods."""

    def test_calculate_frame_time_single_frame(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            t = exporter._calculate_frame_time(0, 1)
            assert t == 0.0

    def test_calculate_frame_time_multi_frame(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            assert exporter._calculate_frame_time(0, 10) == 0.0
            assert exporter._calculate_frame_time(9, 10) == 1.0
            assert exporter._calculate_frame_time(4, 9) == pytest.approx(0.5)

    def test_infer_formats_from_extension(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            assert exporter._infer_formats_from_extension(".svg") == ["svg"]
            assert exporter._infer_formats_from_extension(".png") == ["png"]
            assert exporter._infer_formats_from_extension(".pdf") == ["pdf"]

    def test_infer_formats_invalid_extension(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            with pytest.raises(ValueError):
                exporter._infer_formats_from_extension(".mp3")

    def test_needs_converter(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            assert exporter._needs_converter(["svg"]) == []
            assert exporter._needs_converter(["png"]) == ["png"]
            assert exporter._needs_converter(["svg", "png", "pdf"]) == ["png", "pdf"]


@pytest.mark.unit
class TestVSceneExporterExport:
    """Tests for export methods."""

    def test_export_svg(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            result = exporter.export("test.svg", frame_time=0.0, formats=["svg"])

            assert result.success is True
            assert "svg" in result.files
            mock_scene.to_svg.assert_called()

    def test_export_invalid_frame_time(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)

            with pytest.raises(ValueError):
                exporter.export("test.svg", frame_time=1.5)

    def test_export_png_calls_converter(self, mock_scene, temp_dir):
        mock_converter = MagicMock()
        mock_converter.convert.return_value = {"png": f"{temp_dir}/test.png"}

        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = mock_converter
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            result = exporter.export("test.png", frame_time=0.0, formats=["png"])

            assert result.success is True
            mock_converter.convert.assert_called()


@pytest.mark.unit
class TestVSceneExporterToFrames:
    """Tests for to_frames method."""

    def test_to_frames_invalid_total_frames(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)

            with pytest.raises(ValueError):
                list(exporter.to_frames(temp_dir, total_frames=0))

    def test_to_frames_invalid_format(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)

            with pytest.raises(ValueError):
                list(exporter.to_frames(temp_dir, format="mp4"))

    def test_to_frames_invalid_pattern(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)

            with pytest.raises(ValueError):
                list(exporter.to_frames(temp_dir, filename_pattern="no_placeholder"))

    def test_to_frames_svg_yields_frames(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)

            frames = list(
                exporter.to_frames(temp_dir, total_frames=5, format="svg")
            )
            assert len(frames) == 5
            assert frames[0] == (0, 0.0)
            assert frames[4] == (4, 1.0)


@pytest.mark.unit
class TestVSceneExporterVideo:
    """Tests for video export methods."""

    def test_to_mp4_no_ffmpeg(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            exporter._check_ffmpeg_available = MagicMock(return_value=False)

            with pytest.raises(RuntimeError) as exc_info:
                exporter.to_mp4("test", total_frames=10)
            assert "ffmpeg" in str(exc_info.value)

    def test_to_gif_invalid_frames(self, mock_scene, temp_dir):
        pytest.importorskip("PIL")
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)

            with pytest.raises(ValueError):
                exporter.to_gif("test", total_frames=0)


@pytest.mark.unit
class TestVSceneExporterHTML:
    """Tests for HTML export methods."""

    def test_to_html_invalid_frames(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)

            with pytest.raises(ValueError):
                exporter.to_html("test", total_frames=1)

    def test_to_html_invalid_framerate(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)

            with pytest.raises(ValueError):
                exporter.to_html("test", framerate=0)


@pytest.mark.unit
class TestVSceneExporterOutputPath:
    """Tests for output path generation."""

    def test_generate_output_path_without_timestamp(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(
                mock_scene, output_dir=temp_dir, timestamp_files=False
            )
            path = exporter._generate_output_path("test.svg")
            assert path.name == "test.svg"

    def test_generate_output_path_with_extension_override(self, mock_scene, temp_dir):
        with patch(
            "svan2d.vscene.vscene_exporter.VSceneExporter._init_converter"
        ) as mock_init:
            mock_init.return_value = MagicMock()
            exporter = VSceneExporter(mock_scene, output_dir=temp_dir)
            path = exporter._generate_output_path("test.svg", ".png")
            assert path.suffix == ".png"
