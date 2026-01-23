"""Scene composition and export.

VScene manages elements and renders frames for animation:
- VScene: Container for VElements with rendering and frame generation
- VSceneExporter: Exports scenes to SVG, PNG, PDF, MP4, GIF
- CameraState: State for animated scene-level camera transforms
"""

from .camera_state import CameraState
from .vscene import VScene
from .vscene_exporter import VSceneExporter

__all__ = ["VScene", "VSceneExporter", "CameraState"]
