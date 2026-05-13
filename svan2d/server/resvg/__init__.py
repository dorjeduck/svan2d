"""HTTP rendering server using the Rust `resvg` library via `resvg-py`.

Mirrors the playwright_http server but uses resvg for SVG to PNG conversion.
PNG only; PDF is not supported by resvg.
"""

from .process_manager import ProcessManager
from .render_server import app, create_server

__all__ = ["app", "create_server", "ProcessManager"]
