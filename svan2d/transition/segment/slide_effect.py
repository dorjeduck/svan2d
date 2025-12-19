from enum import Enum


class SlideEffect(Enum):
    """Controls visual effects during slide transitions.

    Members:
        NONE: No effect, instant transition
        FADE: Opacity fades during transition
        SCALE: Element scales during transition
        FADE_SCALE: Combined fade and scale effect
    """

    NONE = "none"
    FADE = "fade"
    SCALE = "scale"
    FADE_SCALE = "fade_scale"
