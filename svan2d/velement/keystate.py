"""KeyState class for explicit keystate specification

Provides a clear, typed alternative to tuple-based keystate specification.
All tuple formats are converted to KeyState objects internally.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Union

from svan2d.component.state.base import State
from svan2d.velement.morphing import MorphingConfig
from svan2d.velement.transition import TransitionConfig


@dataclass
class KeyState:

    state: State
    time: float | None = None
    transition_config: Optional[TransitionConfig] = None
    skip_render_at: bool = False

    def __post_init__(self):
        """Validate time range and morphing configuration"""
        # Validate time if provided
        if self.time is not None:
            if not isinstance(self.time, (int, float)):
                raise TypeError(
                    f"time must be a number, got {type(self.time).__name__}"
                )
            if not (0.0 <= self.time <= 1.0):
                raise ValueError(f"time must be between 0.0 and 1.0, got {self.time}")

        # Validate state
        if not isinstance(self.state, State):
            raise TypeError(
                f"state must be a State instance, got {type(self.state).__name__}"
            )

        # Validate easing dict if provided

        if self.transition_config is not None:

            if self.transition_config.easing_dict is not None and not isinstance(
                self.transition_config.easing_dict, dict
            ):
                raise TypeError(
                    f"easing must be a dict, got {type(self.transition_config.easing_dict).__name__}"
                )

            # Validate morphing configuration if provided
            if self.transition_config.morphing_config is not None:
                if isinstance(self.transition_config.morphing_config, MorphingConfig):
                    # Morphing class - all good
                    pass
                elif isinstance(self.transition_config.morphing_config, dict):
                    # Dict format (deprecated but supported) - validate keys
                    valid_keys = {"mapper", "vertex_aligner"}
                    invalid_keys = (
                        set(self.transition_config.morphing_config.keys()) - valid_keys
                    )
                    if invalid_keys:
                        raise ValueError(
                            f"Invalid morphing keys: {invalid_keys}. "
                            f"Valid keys are: {valid_keys}"
                        )
                else:
                    raise TypeError(
                        f"morphing must be a Morphing instance or dict, "
                        f"got {type(self.transition_config.morphing_config).__name__}"
                    )

    def with_time(self, time: float) -> KeyState:
        """Create a new KeyState with updated time (immutable update)

        Used internally during time distribution to assign calculated times
        to auto-timed keystates.

        Args:
            time: New time value (0.0-1.0)

        Returns:
            New KeyState instance with updated time
        """
        return KeyState(
            state=self.state,
            time=time,
            transition_config=self.transition_config,
            skip_render_at=self.skip_render_at,
        )

    def __repr__(self) -> str:
        """Readable representation showing only non-None attributes"""
        parts = [f"state={self.state.__class__.__name__}(...)"]
        if self.time is not None:
            parts.append(f"time={self.time}")
        if self.transition_config is not None:
            if self.transition_config.easing_dict is not None:
                parts.append(
                    f"easing={{{', '.join(self.transition_config.easing_dict.keys())}}}"
                )
            if self.transition_config.morphing_config is not None:
                if isinstance(self.transition_config.morphing_config, MorphingConfig):
                    morph_parts = []
                    if self.transition_config.morphing_config.mapper is not None:
                        morph_parts.append(
                            f"mapper={type(self.transition_config.morphing_config.mapper).__name__}"
                        )
                    if (
                        self.transition_config.morphing_config.vertex_aligner
                        is not None
                    ):
                        morph_parts.append(
                            f"vertex_aligner={type(self.transition_config.morphing_config.vertex_aligner).__name__}"
                        )
                    parts.append(f"morphing=MorphingConfig({', '.join(morph_parts)})")
                else:
                    parts.append(
                        f"morphing={{{', '.join(self.transition_config.morphing_config.keys())}}}"
                    )
        return f"KeyState({', '.join(parts)})"


KeyStates = list[KeyState]
