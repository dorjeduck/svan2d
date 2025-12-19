"""Segment functions for reusable animation patterns.

Segment functions generate lists of KeyStates for common animation patterns:
- hold: Hold state for a duration
- fade_inout: Fade in, hold, fade out
- bounce: Oscillate between states
- crossfade: Smooth transition between two elements
- swap_positions: Exchange positions with easing
- arc_swap_positions: Exchange positions along arc paths
- slide_hold_slide: Slide in, hold, slide out
- just_slide: Simple slide animation
- linspace: Generate evenly spaced values
"""

from .utils import linspace
from .hold import hold
from .fade_inout import fade_inout
from .bounce import bounce
from .crossfade import crossfade
from .swap_positions import swap_positions
from .arc_swap_positions import arc_swap_positions
from .slide_hold_slide import slide_hold_slide
from .just_slide import just_slide
from .slide_effect import SlideEffect

__all__ = [
    "linspace",
    "hold",
    "fade_inout",
    "bounce",
    "crossfade",
    "swap_positions",
    "arc_swap_positions",
    "slide_hold_slide",
    "SlideEffect",
    "just_slide",
]
