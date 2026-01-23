"""VElement package - animatable elements with keystate-based animation.

This package provides the core animation system for svan2d:
- VElement: Combines renderer + state(s) for static or animated rendering
- VElementGroup: Groups multiple elements with shared transforms
- KeyState: Explicit keystate specification with timing and transitions
- TransitionConfig: Per-segment easing, curves, and morphing configuration
- Segment functions: Reusable timeline patterns (hold, fade_inout, bounce, etc.)
"""

from .base_velement import BaseVElement
from .keystate import KeyState
from .morphing import MorphingConfig
from .segments import bounce, crossfade, fade_inout, hold, linspace
from .transition import TransitionConfig
from .velement import VElement
from .velement_group import VElementGroup, VElementGroupState

__all__ = [
    "BaseVElement",
    "VElement",
    "VElementGroup",
    "VElementGroupState",
    "KeyState",
    "MorphingConfig",
    "TransitionConfig",
    "fade_inout",
    "hold",
    "linspace",
    "crossfade",
    "bounce",
]
