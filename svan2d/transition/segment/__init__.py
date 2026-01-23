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


def linspace(n: int, t1: float = 0.0, t2: float = 1.0) -> list[float]:
    """Generate n evenly spaced values from t1 to t2 (inclusive)."""
    if n == 1:
        return [(t1 + t2) / 2]

    dif = t2 - t1
    return [t1 + i * dif / (n - 1) for i in range(n)]
from .arc_swap_positions import arc_swap_positions
from .bounce import bounce
from .crossfade import crossfade
from .fade_inout import fade_inout
from .hold import hold
from .just_slide import just_slide
from .slide_effect import SlideEffect
from .slide_hold_slide import slide_hold_slide
from .swap_positions import swap_positions

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
