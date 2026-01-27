"""Scene transition effects for combining multiple VScenes.

Scene transitions control how one scene transitions to another,
enabling effects like fades, wipes, slides, zooms, and iris reveals.

Available transitions:
- Fade: Opacity-based crossfade between scenes
- Wipe: Directional reveal using clip paths
- Slide: Transform-based scene movement
- Zoom: Scale transform with opacity blend
- Iris: Circular clip path reveal
- Dissolve: Random pixel dissolve (requires rasterization)
"""

from .base import RenderContext, SceneTransition
from .fade import Fade
from .iris import Iris
from .slide import Slide
from .wipe import Wipe
from .zoom import Zoom

__all__ = [
    # Base classes
    "SceneTransition",
    "RenderContext",
    # Transitions
    "Fade",
    "Wipe",
    "Slide",
    "Zoom",
    "Iris",
]
