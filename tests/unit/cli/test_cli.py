"""Tests for svan2d.cli module."""

import pytest

# Skip if click is not installed (it's a dev dependency)
click = pytest.importorskip("click", reason="click not installed")
from click.testing import CliRunner

# Skip if fastapi is not installed since CLI imports devserver commands
pytest.importorskip("fastapi", reason="fastapi not installed (optional dependency)")

from svan2d.cli.main import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.mark.unit
class TestCLIBasics:
    """Tests for basic CLI functionality."""

    def test_cli_without_args_shows_help(self, runner):
        result = runner.invoke(cli, [])
        # Exit code 0 or 2 (missing command) are both acceptable
        assert result.exit_code in [0, 2]
        # Check for some output
        assert len(result.output) > 0 or "Usage" in result.output or "Svan2D" in result.output

    def test_cli_help_flag(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Options:" in result.output

    def test_cli_version_flag(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        # Should show version number
        assert "0." in result.output or "svan2d" in result.output.lower()


@pytest.mark.unit
class TestPlaywrightServerCommands:
    """Tests for playwright-server CLI commands."""

    def test_playwright_server_help(self, runner):
        result = runner.invoke(cli, ["playwright-server", "--help"])
        assert result.exit_code == 0
        assert "start" in result.output.lower() or "stop" in result.output.lower()

    def test_playwright_server_status_runs(self, runner):
        result = runner.invoke(cli, ["playwright-server", "status"])
        # Should run without crash, may show "not running"
        assert result.exit_code in [0, 1]  # Success or expected failure


@pytest.mark.unit
class TestServeCommand:
    """Tests for serve CLI command."""

    def test_serve_help(self, runner):
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_serve_requires_file(self, runner):
        result = runner.invoke(cli, ["serve"])
        # Should show help or error about missing file
        # Exit code 2 is common for missing required argument
        assert result.exit_code in [0, 2]


@pytest.mark.unit
class TestCLIModuleImports:
    """Tests for CLI module imports."""

    def test_main_module_importable(self):
        from svan2d.cli.main import cli
        assert cli is not None

    def test_devserver_commands_importable(self):
        from svan2d.cli.devserver_commands import serve
        assert serve is not None

    def test_playwright_commands_importable(self):
        from svan2d.cli.playwright_server_commands import playwright_server
        assert playwright_server is not None
