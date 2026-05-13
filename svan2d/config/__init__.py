"""Svan2D configuration system

This module provides a global configuration system for svan2d, allowing users
to customize default values via TOML configuration files.

Usage:
    # Get current configuration
    from svan2d.config import get_config, ConfigKey
    config = get_config()
    width = config.get(ConfigKey.SCENE_WIDTH)

    # Load custom configuration
    from svan2d.config import load_config
    load_config('my_config.toml')

    # Reset to system defaults
    from svan2d.config import reset_config
    reset_config()
"""

from pathlib import Path

from .config import Svan2DConfig
from .config_key import ConfigKey

# Global configuration instance
_global_config: Svan2DConfig | None = None


def get_config() -> Svan2DConfig:
    """Return the global Svan2DConfig, initializing from defaults and user config on first call.

    Example:
        config = get_config()
        config.get(ConfigKey.SCENE_WIDTH)  # 800
    """
    global _global_config

    if _global_config is None:
        # Initialize with defaults and user config if available
        _global_config = Svan2DConfig.load_with_overrides()

    return _global_config


def load_config(path: Path | str | None = None):
    """Load configuration from file

    If path is None, searches for config in standard locations:
    - ./svan2d.toml
    - ~/.config/svan2d/config.toml
    - ~/.svan2d.toml

    Args:
        path: Optional path to configuration file

    Example:
        from svan2d.config import load_config
        load_config('my_project_config.toml')
    """
    global _global_config
    _global_config = Svan2DConfig.load_with_overrides(path)


def reset_config():
    """Reset the global configuration to system defaults."""
    global _global_config
    _global_config = Svan2DConfig.load_defaults()


def create_config_template(path: Path | str = "svan2d.toml"):
    """Create a template configuration file

    Copies the system defaults to a new file that users can customize.

    Args:
        path: Path where to create the template (default: "svan2d.toml")

    Example:
        from svan2d.config import create_config_template
        create_config_template("my_config.toml")
    """
    import shutil

    defaults_path = Path(__file__).parent / "defaults.toml"
    dest_path = Path(path)

    shutil.copy(defaults_path, dest_path)
    print(f"Created config template at: {dest_path}")


# Initialize global config on module import
_global_config = Svan2DConfig.load_with_overrides()


__all__ = [
    "Svan2DConfig",
    "ConfigKey",
    "get_config",
    "load_config",
    "reset_config",
    "create_config_template",
]
