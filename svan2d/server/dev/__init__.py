"""
Svan2D Development Server

Lightweight development server for live animation preview with hot-reload.

Note: This module requires optional dependencies (fastapi, uvicorn, watchdog).
Install with: pip install svan2d[devserver]
"""

# Lazy imports to avoid requiring fastapi at module import time
def __getattr__(name: str):
    if name == "create_app":
        from .server import create_app
        return create_app
    if name == "animation":
        from .module_loader import animation
        return animation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["create_app", "animation"]
