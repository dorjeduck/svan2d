"""Svan2D configuration system

This module provides a global configuration system for svan2D, allowing users
to customize default values via TOML configuration files.

Usage:
    # Get current configuration
    from svan2D.config import get_config, ConfigKey
    config = get_config()
    width = config.get(ConfigKey.SCENE_WIDTH)

    # Load custom configuration
    from svan2D.config import load_config
    load_config('my_config.toml')

    # Reset to system defaults
    from svan2D.config import reset_config
    reset_config()
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from .config import Svan2DConfig
from .config_key import ConfigKey

# Global configuration instance
_global_config: Optional[Svan2DConfig] = None


def get_config() -> Svan2DConfig:
    """Get the global configuration instance

    Returns:
        Global Svan2DConfig instance

    Example:
        >>> from svan2D.config import get_config, ConfigKey
        >>> config = get_config()
        >>> width = config.get(ConfigKey.SCENE_WIDTH)
        >>> width
        800
    """
    global _global_config

    if _global_config is None:
        # Initialize with defaults and user config if available
        _global_config = Svan2DConfig.load_with_overrides()

    return _global_config


def load_config(path: Optional[Path | str] = None):
    """Load configuration from file

    If path is None, searches for config in standard locations:
    - ./svan2D.toml
    - ~/.config/svan2D/config.toml
    - ~/.svan2D.toml

    Args:
        path: Optional path to configuration file

    Example:
        >>> from svan2D.config import load_config
        >>> load_config('my_project_config.toml')
    """
    global _global_config
    _global_config = Svan2DConfig.load_with_overrides(path)


def reset_config():
    """Reset configuration to system defaults

    Example:
        >>> from svan2D.config import reset_config
        >>> reset_config()
    """
    global _global_config
    _global_config = Svan2DConfig.load_defaults()


def create_config_template(path: Path | str = "svan2D.toml"):
    """Create a template configuration file

    Copies the system defaults to a new file that users can customize.

    Args:
        path: Path where to create the template (default: "svan2D.toml")

    Example:
        >>> from svan2D.config import create_config_template
        >>> create_config_template("my_config.toml")
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
