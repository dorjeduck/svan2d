"""Scene composition and export.

VScene manages elements and renders frames for animation:
- VScene: Container for VElements with rendering and frame generation
- VSceneExporter: Exports scenes to SVG, PNG, PDF, MP4, GIF
- VSceneSequence: Sequence multiple VScenes with transitions
- VSceneComposite: Spatial composition of multiple scenes (horizontal/vertical stacking)
- CameraState: State for animated scene-level camera transforms
"""

from .camera_state import CameraState
from svan2d.core.enums import Origin
from .vscene import VScene
from .vscene_composite import VSceneComposite
from .vscene_exporter import VSceneExporter
from .vscene_sequence import VSceneSequence

__all__ = [
    "Origin",
    "VScene",
    "VSceneExporter",
    "VSceneSequence",
    "VSceneComposite",
    "CameraState",
]
