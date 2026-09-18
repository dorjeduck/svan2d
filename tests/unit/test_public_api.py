"""Every name a package lists in __all__ must exist, or `import *` from it fails."""

import importlib

import pytest

PACKAGES = [
    "svan2d",
    "svan2d.primitive",
    "svan2d.primitive.renderer",
    "svan2d.primitive.state",
    "svan2d.primitive.effect",
    "svan2d.transition",
    "svan2d.transition.easing",
    "svan2d.transition.interpolators",
]


@pytest.mark.parametrize("package", PACKAGES)
def test_all_names_exist(package):
    module = importlib.import_module(package)
    missing = [name for name in module.__all__ if not hasattr(module, name)]
    assert missing == []


def test_star_renderer_exported():
    """renderer/star.py defines StarRenderer; the package exports it like every other renderer."""
    renderer = importlib.import_module("svan2d.primitive.renderer")
    assert "StarRenderer" in renderer.__all__
