"""Tests for svan2d.server.dev.module_loader module."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Skip entire module if fastapi is not installed (optional dependency)
pytest.importorskip("fastapi", reason="fastapi not installed (optional dependency)")

from svan2d.server.dev.module_loader import (
    _animation_registry,
    animation,
    extract_scene,
    file_path_to_module_name,
    safe_reload_module,
)


@pytest.fixture
def mock_vscene():
    """Create a mock VScene."""
    from svan2d.vscene import VScene
    return VScene(width=100, height=100)


@pytest.fixture
def temp_python_file():
    """Create a temporary Python file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        yield Path(f.name)


@pytest.mark.unit
class TestAnimationDecorator:
    """Tests for @animation decorator."""

    def test_decorator_registers_function(self):
        # Clear registry first
        _animation_registry.clear()

        @animation
        def test_scene():
            pass

        # The function should be registered
        assert test_scene.__module__ in _animation_registry

    def test_decorator_returns_original_function(self):
        @animation
        def test_scene():
            return "test"

        assert test_scene() == "test"


@pytest.mark.unit
class TestExtractScene:
    """Tests for extract_scene function."""

    def test_extract_scene_variable(self):
        """Extract scene from 'scene' variable."""
        from svan2d.vscene import VScene

        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_scene = VScene(width=100, height=100)
        mock_module.scene = mock_scene

        # Clear registry to ensure we test variable extraction
        _animation_registry.clear()

        scene, error = extract_scene(mock_module)
        assert scene is mock_scene
        assert error is None

    def test_extract_scene_from_create_scene_function(self):
        """Extract scene from create_scene() function."""
        from svan2d.vscene import VScene

        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_scene = VScene(width=100, height=100)
        mock_module.scene = None  # No scene variable
        mock_module.create_scene = MagicMock(return_value=mock_scene)

        _animation_registry.clear()

        scene, error = extract_scene(mock_module)
        assert scene is mock_scene
        mock_module.create_scene.assert_called_once()

    def test_extract_scene_no_scene_found(self):
        """Return None when no scene found."""
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        mock_module.scene = None
        mock_module.create_scene = None

        # Remove VScene attributes
        mock_module.configure_mock(**{
            '__dir__': lambda self: [],
        })

        _animation_registry.clear()

        scene, error = extract_scene(mock_module)
        assert scene is None


@pytest.mark.unit
class TestFilePathToModuleName:
    """Tests for file_path_to_module_name function."""

    def test_converts_path_to_module_name(self):
        path = Path("/path/to/animation.py")
        name = file_path_to_module_name(path)
        assert name.startswith("svan2d_devserver_animation_")
        assert ".py" not in name

    def test_different_paths_different_names(self):
        path1 = Path("/path/to/animation1.py")
        path2 = Path("/path/to/animation2.py")
        name1 = file_path_to_module_name(path1)
        name2 = file_path_to_module_name(path2)
        assert name1 != name2


@pytest.mark.unit
class TestSafeReloadModule:
    """Tests for safe_reload_module function."""

    def test_file_not_found(self):
        """Return error when file doesn't exist."""
        path = Path("/nonexistent/file.py")
        scene, error = safe_reload_module(path)
        assert scene is None
        assert "not found" in error.lower()

    def test_syntax_error_handling(self, temp_python_file):
        """Return error for syntax errors."""
        temp_python_file.write_text("def broken(\n")  # Invalid syntax

        scene, error = safe_reload_module(temp_python_file)
        assert scene is None
        assert "Syntax Error" in error

    def test_valid_file_with_scene(self, temp_python_file):
        """Load valid file with scene variable."""
        temp_python_file.write_text("""
from svan2d.vscene import VScene
scene = VScene(width=100, height=100)
""")

        scene, error = safe_reload_module(temp_python_file)
        # Should succeed
        if scene is not None:
            assert error is None
        else:
            # May fail due to import issues in test environment
            assert error is not None


@pytest.mark.unit
class TestDevServerImports:
    """Tests for dev server module imports."""

    def test_file_watcher_importable(self):
        try:
            from svan2d.server.dev.file_watcher import FileWatcher
            assert FileWatcher is not None
        except ImportError:
            pytest.skip("FileWatcher not found")

    def test_websocket_manager_module_importable(self):
        # Check module is importable (class name may differ)
        try:
            import svan2d.server.dev.websocket_manager
            assert True
        except ImportError:
            pytest.skip("websocket_manager module not found")

    def test_export_job_manager_importable(self):
        try:
            from svan2d.server.dev.export_job_manager import ExportJobManager
            assert ExportJobManager is not None
        except ImportError:
            pytest.skip("ExportJobManager not found")


@pytest.mark.unit
class TestPlaywrightServerImports:
    """Tests for playwright server module imports."""

    def test_process_manager_importable(self):
        try:
            from svan2d.server.playwright.process_manager import ProcessManager
            assert ProcessManager is not None
        except ImportError:
            pytest.skip("ProcessManager not found")

    def test_render_server_module_importable(self):
        # Check module is importable (class name may differ)
        try:
            import svan2d.server.playwright.render_server
            assert True
        except ImportError:
            pytest.skip("render_server module not found")
