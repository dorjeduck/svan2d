"""VSceneSequence - sequence multiple VScenes with transitions.

Enables combining multiple scenes with animated transitions between them,
such as fades, wipes, slides, and more.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Union

import drawsvg as dw

from svan2d.core import get_logger
from svan2d.transition.scene.base import RenderContext, SceneTransition
from svan2d.core.enums import Origin

if TYPE_CHECKING:
    from svan2d.vscene import VScene

logger = get_logger()


@dataclass
class _SceneEntry:
    """Internal representation of a scene in the sequence."""

    scene: "VScene"
    duration: float  # Relative duration (will be normalized)


@dataclass
class _TransitionEntry:
    """Internal representation of a transition in the sequence."""

    transition: SceneTransition


@dataclass
class _TimeSegment:
    """Computed time segment for a scene or transition."""

    start: float  # Global start time (0.0-1.0)
    end: float  # Global end time (0.0-1.0)
    scene: Optional["VScene"] = None
    scene_out: Optional["VScene"] = None
    scene_in: Optional["VScene"] = None
    transition: Optional[SceneTransition] = None
    is_transition: bool = False
    # For overlapping transitions: store scene time ranges for continuous mapping
    scene_out_range: Optional[tuple[float, float]] = None
    scene_in_range: Optional[tuple[float, float]] = None


class VSceneSequence:
    """Sequence of VScenes with transitions between them.

    VSceneSequence provides a builder API for combining multiple scenes
    with animated transitions. It handles time mapping so each scene's
    internal time (0.0-1.0) is correctly mapped to the sequence timeline.
    All methods return new instances (immutable pattern).

    Example:
        sequence = (
            VSceneSequence()
            .scene(intro_scene, duration=0.3)
            .transition(Fade(duration=0.1))
            .scene(main_scene, duration=0.4)
            .transition(Wipe(direction="left", duration=0.1))
            .scene(outro_scene, duration=0.2)
        )
        sequence.to_mp4("output.mp4", total_frames=120, framerate=30)
    """

    def __init__(
        self,
        width: Optional[float] = None,
        height: Optional[float] = None,
        origin: Optional[Origin] = None,
        *,
        # Private param for _replace - don't use directly
        _entries: Optional[List[Union[_SceneEntry, _TransitionEntry]]] = None,
    ) -> None:
        """Initialize an empty scene sequence.

        Args:
            width: Override width (default: use first scene's width)
            height: Override height (default: use first scene's height)
            origin: Override origin mode (default: use first scene's origin)
        """
        self._entries: List[Union[_SceneEntry, _TransitionEntry]] = _entries if _entries is not None else []
        self._segments: Optional[List[_TimeSegment]] = None
        self._width = width
        self._height = height
        self._origin = origin

    def _replace(
        self,
        *,
        entries: Optional[List[Union[_SceneEntry, _TransitionEntry]]] = None,
    ) -> "VSceneSequence":
        """Return a new VSceneSequence with specified attributes replaced."""
        new = VSceneSequence.__new__(VSceneSequence)
        new._entries = entries if entries is not None else self._entries.copy()
        new._segments = None  # Always invalidate cached segments
        new._width = self._width
        new._height = self._height
        new._origin = self._origin
        return new

    def scene(self, scene: "VScene", duration: float = 1.0) -> "VSceneSequence":
        """Add a scene to the sequence. Returns new VSceneSequence.

        Args:
            scene: The VScene to add
            duration: Relative duration weight for this scene

        Returns:
            New VSceneSequence with scene added

        Raises:
            ValueError: If duration is not positive or if a scene follows
                       another scene without a transition
        """
        if duration <= 0:
            raise ValueError(f"duration must be positive, got {duration}")

        # Check for consecutive scenes without transition
        if self._entries and isinstance(self._entries[-1], _SceneEntry):
            raise ValueError(
                "Cannot add consecutive scenes without a transition. "
                "Use .transition() between scenes."
            )

        new_entries = self._entries + [_SceneEntry(scene=scene, duration=duration)]
        return self._replace(entries=new_entries)

    def transition(self, transition: SceneTransition) -> "VSceneSequence":
        """Add a transition between scenes. Returns new VSceneSequence.

        Args:
            transition: The SceneTransition to apply

        Returns:
            New VSceneSequence with transition added

        Raises:
            ValueError: If no scene has been added yet, or if consecutive
                       transitions are added
        """
        if not self._entries:
            raise ValueError(
                "Cannot add transition before any scene. Add a scene first."
            )

        if isinstance(self._entries[-1], _TransitionEntry):
            raise ValueError(
                "Cannot add consecutive transitions. Add a scene between transitions."
            )

        new_entries = self._entries + [_TransitionEntry(transition=transition)]
        return self._replace(entries=new_entries)

    @property
    def width(self) -> float:
        """Get the sequence width (from first scene or override)."""
        if self._width is not None:
            return self._width
        for entry in self._entries:
            if isinstance(entry, _SceneEntry):
                return entry.scene.width
        return 800.0  # Default fallback

    @property
    def height(self) -> float:
        """Get the sequence height (from first scene or override)."""
        if self._height is not None:
            return self._height
        for entry in self._entries:
            if isinstance(entry, _SceneEntry):
                return entry.scene.height
        return 800.0  # Default fallback

    @property
    def origin(self) -> Origin:
        """Get the sequence origin mode (from first scene or override)."""
        if self._origin is not None:
            return self._origin
        for entry in self._entries:
            if isinstance(entry, _SceneEntry):
                return Origin(entry.scene.origin)
        return Origin.CENTER  # Default fallback

    def _compute_segments(self) -> List[_TimeSegment]:
        """Compute time segments for all scenes and transitions.

        Timeline model:
        - Each scene plays its full animation (t=0.0 to t=1.0) during its segment
        - Non-overlapping transitions: happen BETWEEN scenes (add to total duration)
          - scene_out is at t=1.0, scene_in is at t=0.0
        - Overlapping transitions: happen at scene boundaries (don't add duration)
          - Both scenes continue animating with continuous time mapping

        Returns:
            List of _TimeSegment with computed time ranges
        """
        if self._segments is not None:
            return self._segments

        if not self._entries:
            self._segments = []
            return self._segments

        # Collect scenes and transitions
        scenes: List[_SceneEntry] = []
        transitions: List[Optional[SceneTransition]] = []

        for entry in self._entries:
            if isinstance(entry, _SceneEntry):
                scenes.append(entry)
                transitions.append(None)  # Placeholder
            elif isinstance(entry, _TransitionEntry):
                if transitions:
                    transitions[-1] = entry.transition

        # Handle trailing transition (ignored - no scene after)
        if isinstance(self._entries[-1], _TransitionEntry):
            transitions = transitions[:-1]

        if not scenes:
            self._segments = []
            return self._segments

        # Calculate total duration
        # Only non-overlapping transitions add to total duration
        total_scene_duration = sum(s.duration for s in scenes)
        total_transition_duration = sum(
            t.duration
            for i, t in enumerate(transitions)
            if t is not None and not t.overlapping and i < len(scenes) - 1
        )

        # Normalize durations to fit in 0.0-1.0
        total = total_scene_duration + total_transition_duration
        scale = 1.0 / total if total > 0 else 1.0

        # First pass: compute scene ranges
        scene_ranges: List[tuple[float, float]] = []
        current_time = 0.0

        for i, scene_entry in enumerate(scenes):
            scene_duration = scene_entry.duration * scale
            transition = transitions[i] if i < len(transitions) else None
            has_next = i < len(scenes) - 1

            scene_start = current_time
            scene_end = current_time + scene_duration
            scene_ranges.append((scene_start, scene_end))
            current_time = scene_end

            # Only non-overlapping transitions add time
            if transition and has_next and not transition.overlapping:
                transition_duration = transition.duration * scale
                current_time += transition_duration

        # Second pass: build segments
        segments: List[_TimeSegment] = []
        current_time = 0.0

        for i, scene_entry in enumerate(scenes):
            scene_start, scene_end = scene_ranges[i]
            transition = transitions[i] if i < len(transitions) else None
            has_next = i < len(scenes) - 1

            # Scene segment
            segments.append(
                _TimeSegment(
                    start=scene_start,
                    end=scene_end,
                    scene=scene_entry.scene,
                    is_transition=False,
                )
            )

            # Transition segment (if present and not last scene)
            if transition and has_next:
                _, next_scene_end = scene_ranges[i + 1]

                if transition.overlapping:
                    # Overlapping: transition straddles scene boundary
                    # Transition duration is a proportion of total scene time
                    trans_duration = transition.duration * scale
                    trans_half = trans_duration / 2
                    trans_start = scene_end - trans_half
                    trans_end = scene_end + trans_half
                    # Clamp to valid range
                    trans_start = max(scene_start, trans_start)
                    trans_end = min(next_scene_end, trans_end)
                else:
                    # Non-overlapping: transition follows scene_out
                    transition_duration = transition.duration * scale
                    trans_start = scene_end
                    trans_end = scene_end + transition_duration

                segments.append(
                    _TimeSegment(
                        start=trans_start,
                        end=trans_end,
                        scene_out=scene_entry.scene,
                        scene_in=scenes[i + 1].scene,
                        transition=transition,
                        is_transition=True,
                        scene_out_range=scene_ranges[i],
                        scene_in_range=scene_ranges[i + 1],
                    )
                )

        self._segments = segments
        return self._segments

    def _get_segment_at_time(self, frame_time: float) -> Optional[_TimeSegment]:
        """Find the appropriate segment for a given frame time.

        For transition periods, returns the transition segment.
        For non-transition periods, returns the scene segment.

        Args:
            frame_time: Global time in the sequence (0.0-1.0)

        Returns:
            The segment containing this time, or None if no segments
        """
        segments = self._compute_segments()
        if not segments:
            return None

        # Clamp time to valid range
        frame_time = max(0.0, min(1.0, frame_time))

        # Check transitions first (they take priority during overlap)
        for seg in segments:
            if seg.is_transition and seg.start <= frame_time <= seg.end:
                return seg

        # Then check scenes
        for seg in segments:
            if not seg.is_transition and seg.start <= frame_time <= seg.end:
                return seg

        # Fallback to last segment
        return segments[-1] if segments else None

    def _map_time_to_scene(
        self, frame_time: float, segment: _TimeSegment
    ) -> float:
        """Map global frame time to scene-local time (0.0-1.0).

        Args:
            frame_time: Global time in the sequence (0.0-1.0)
            segment: The scene segment

        Returns:
            Local time within the scene (0.0-1.0)
        """
        if segment.end == segment.start:
            return 0.0

        # Linear mapping from segment time range to 0.0-1.0
        local_t = (frame_time - segment.start) / (segment.end - segment.start)
        return max(0.0, min(1.0, local_t))

    def to_drawing(
        self,
        frame_time: float = 0.0,
        render_scale: float = 1.0,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ) -> dw.Drawing:
        """Render the sequence at a specific time point.

        Args:
            frame_time: Time point to render (0.0 to 1.0)
            render_scale: Scale factor for rendering
            width: Unused, for VSceneExporter compatibility
            height: Unused, for VSceneExporter compatibility

        Returns:
            A drawsvg Drawing

        Raises:
            ValueError: If the sequence is empty or frame_time is invalid
        """
        _ = width, height  # Unused, for API compatibility
        if not self._entries:
            raise ValueError("Cannot render empty sequence. Add scenes first.")

        if not 0.0 <= frame_time <= 1.0:
            raise ValueError(
                f"frame_time must be between 0.0 and 1.0, got {frame_time}"
            )

        segment = self._get_segment_at_time(frame_time)
        if segment is None:
            raise ValueError("No segment found for frame_time")

        ctx = RenderContext(
            width=self.width,
            height=self.height,
            render_scale=render_scale,
            origin=self.origin,
        )

        if segment.is_transition:
            # Render transition
            assert segment.transition is not None
            assert segment.scene_out is not None
            assert segment.scene_in is not None

            # Calculate progress within transition
            if segment.end == segment.start:
                progress = 0.0
            else:
                progress = (frame_time - segment.start) / (segment.end - segment.start)
            progress = max(0.0, min(1.0, progress))

            # Apply transition easing
            eased_progress = segment.transition.easing(progress)

            if segment.transition.overlapping:
                # Overlapping mode: continuous time mapping from scene ranges
                assert segment.scene_out_range is not None
                assert segment.scene_in_range is not None

                out_start, out_end = segment.scene_out_range
                in_start, in_end = segment.scene_in_range

                # Map global time to each scene's local time
                if out_end > out_start:
                    time_out = (frame_time - out_start) / (out_end - out_start)
                    time_out = max(0.0, min(1.0, time_out))
                else:
                    time_out = 1.0

                if in_end > in_start:
                    time_in = (frame_time - in_start) / (in_end - in_start)
                    time_in = max(0.0, min(1.0, time_in))
                else:
                    time_in = 0.0
            else:
                # Static mode: blend END of scene_out with START of scene_in
                time_out = 1.0
                time_in = 0.0

            return segment.transition.composite(
                scene_out=segment.scene_out,
                scene_in=segment.scene_in,
                progress=eased_progress,
                time_out=time_out,
                time_in=time_in,
                ctx=ctx,
            )
        else:
            # Render scene directly
            assert segment.scene is not None
            scene_time = self._map_time_to_scene(frame_time, segment)
            return segment.scene.to_drawing(
                frame_time=scene_time,
                render_scale=render_scale,
            )

    def to_svg(
        self,
        frame_time: float = 0.0,
        render_scale: float = 1.0,
        width: Optional[float] = None,
        height: Optional[float] = None,
        filename: Optional[str] = None,
        log: bool = True,
    ) -> str:
        """Render the sequence to SVG at a specific time point.

        Args:
            frame_time: Time point to render (0.0 to 1.0)
            render_scale: Scale factor for rendering
            width: Unused, for VSceneExporter compatibility
            height: Unused, for VSceneExporter compatibility
            filename: Optional filename to save SVG to
            log: Whether to log the save operation

        Returns:
            SVG string
        """
        _ = width, height  # Unused, for API compatibility
        drawing = self.to_drawing(frame_time=frame_time, render_scale=render_scale)
        svg_string: str = drawing.as_svg()  # type: ignore[assignment]

        if filename:
            drawing.save_svg(filename)
            if log:
                logger.info(f'SVG exported to "{filename}"')

        return svg_string

    def __repr__(self) -> str:
        scene_count = sum(1 for e in self._entries if isinstance(e, _SceneEntry))
        trans_count = sum(1 for e in self._entries if isinstance(e, _TransitionEntry))
        return f"VSceneSequence(scenes={scene_count}, transitions={trans_count})"
