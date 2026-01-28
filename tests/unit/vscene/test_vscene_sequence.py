"""Tests for svan2d.vscene.vscene_sequence module."""

import pytest

from svan2d.core.color import Color
from svan2d.transition import easing
from svan2d.transition.scene import Fade, Iris, Slide, Wipe, Zoom
from svan2d.transition.scene.base import RenderContext
from svan2d.vscene import VScene, VSceneSequence


@pytest.fixture
def simple_scene_1():
    """Create a simple scene for testing."""
    return VScene(width=400, height=300, background=Color("#ff0000"))


@pytest.fixture
def simple_scene_2():
    """Create another simple scene for testing."""
    return VScene(width=400, height=300, background=Color("#00ff00"))


@pytest.fixture
def simple_scene_3():
    """Create a third simple scene for testing."""
    return VScene(width=400, height=300, background=Color("#0000ff"))


# ==============================================================================
# VSceneSequence Creation Tests
# ==============================================================================


@pytest.mark.unit
class TestVSceneSequenceCreation:
    """Tests for VSceneSequence initialization."""

    def test_create_empty_sequence(self):
        seq = VSceneSequence()
        assert repr(seq) == "VSceneSequence(scenes=0, transitions=0)"

    def test_create_with_custom_dimensions(self):
        seq = VSceneSequence(width=800, height=600)
        assert seq.width == 800
        assert seq.height == 600

    def test_create_with_custom_origin(self):
        seq = VSceneSequence(origin="top-left")
        assert seq.origin == "top-left"


@pytest.mark.unit
class TestVSceneSequenceBuilder:
    """Tests for VSceneSequence builder API."""

    def test_add_single_scene(self, simple_scene_1):
        seq = VSceneSequence().scene(simple_scene_1, duration=1.0)
        assert "scenes=1" in repr(seq)

    def test_add_scene_returns_new_instance(self, simple_scene_1):
        seq = VSceneSequence()
        result = seq.scene(simple_scene_1)
        # Now returns a new instance, not self
        assert isinstance(result, VSceneSequence)
        assert "scenes=1" in repr(result)
        assert "scenes=0" in repr(seq)  # Original unchanged

    def test_add_transition_returns_new_instance(self, simple_scene_1, simple_scene_2):
        seq = VSceneSequence().scene(simple_scene_1)
        result = seq.transition(Fade())
        # Now returns a new instance, not self
        assert isinstance(result, VSceneSequence)
        assert "transitions=1" in repr(result)

    def test_chain_scenes_with_transitions(
        self, simple_scene_1, simple_scene_2, simple_scene_3
    ):
        seq = (
            VSceneSequence()
            .scene(simple_scene_1, duration=0.3)
            .transition(Fade(duration=0.1))
            .scene(simple_scene_2, duration=0.4)
            .transition(Wipe(duration=0.1))
            .scene(simple_scene_3, duration=0.2)
        )
        assert "scenes=3" in repr(seq)
        assert "transitions=2" in repr(seq)

    def test_consecutive_scenes_raises(self, simple_scene_1, simple_scene_2):
        seq = VSceneSequence().scene(simple_scene_1)
        with pytest.raises(ValueError, match="consecutive scenes"):
            seq.scene(simple_scene_2)

    def test_consecutive_transitions_raises(self, simple_scene_1):
        seq = VSceneSequence().scene(simple_scene_1).transition(Fade())
        with pytest.raises(ValueError, match="consecutive transitions"):
            seq.transition(Wipe())

    def test_transition_before_scene_raises(self):
        seq = VSceneSequence()
        with pytest.raises(ValueError, match="before any scene"):
            seq.transition(Fade())

    def test_invalid_scene_duration_raises(self, simple_scene_1):
        seq = VSceneSequence()
        with pytest.raises(ValueError, match="positive"):
            seq.scene(simple_scene_1, duration=0)
        with pytest.raises(ValueError, match="positive"):
            seq.scene(simple_scene_1, duration=-1)


@pytest.mark.unit
class TestVSceneSequenceProperties:
    """Tests for VSceneSequence property accessors."""

    def test_dimensions_from_first_scene(self, simple_scene_1, simple_scene_2):
        seq = (
            VSceneSequence()
            .scene(simple_scene_1)
            .transition(Fade())
            .scene(simple_scene_2)
        )
        assert seq.width == simple_scene_1.width
        assert seq.height == simple_scene_1.height

    def test_dimensions_override(self, simple_scene_1):
        seq = VSceneSequence(width=1920, height=1080).scene(simple_scene_1)
        assert seq.width == 1920
        assert seq.height == 1080

    def test_origin_from_first_scene(self, simple_scene_1):
        seq = VSceneSequence().scene(simple_scene_1)
        assert seq.origin == simple_scene_1.origin

    def test_default_fallback_values(self):
        seq = VSceneSequence()
        assert seq.width == 800.0
        assert seq.height == 800.0
        assert seq.origin == "center"


# ==============================================================================
# VSceneSequence Rendering Tests
# ==============================================================================


@pytest.mark.unit
class TestVSceneSequenceRendering:
    """Tests for VSceneSequence rendering methods."""

    def test_to_drawing_empty_raises(self):
        seq = VSceneSequence()
        with pytest.raises(ValueError, match="empty sequence"):
            seq.to_drawing(frame_time=0.5)

    def test_to_drawing_invalid_time_raises(self, simple_scene_1):
        seq = VSceneSequence().scene(simple_scene_1)
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            seq.to_drawing(frame_time=-0.1)
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            seq.to_drawing(frame_time=1.5)

    def test_to_drawing_single_scene(self, simple_scene_1):
        seq = VSceneSequence().scene(simple_scene_1)
        drawing = seq.to_drawing(frame_time=0.5)
        assert drawing is not None

    def test_to_drawing_multiple_scenes(
        self, simple_scene_1, simple_scene_2, simple_scene_3
    ):
        seq = (
            VSceneSequence()
            .scene(simple_scene_1, duration=0.3)
            .transition(Fade(duration=0.1))
            .scene(simple_scene_2, duration=0.3)
            .transition(Fade(duration=0.1))
            .scene(simple_scene_3, duration=0.2)
        )
        # Test at various points
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            drawing = seq.to_drawing(frame_time=t)
            assert drawing is not None

    def test_to_svg_returns_string(self, simple_scene_1):
        seq = VSceneSequence().scene(simple_scene_1)
        svg = seq.to_svg(frame_time=0.5)
        assert isinstance(svg, str)
        assert "<svg" in svg

    def test_to_drawing_with_render_scale(self, simple_scene_1):
        seq = VSceneSequence().scene(simple_scene_1)
        drawing = seq.to_drawing(frame_time=0.5, render_scale=2.0)
        assert drawing is not None


# ==============================================================================
# SceneTransition Base Class Tests
# ==============================================================================


@pytest.mark.unit
class TestSceneTransitionBase:
    """Tests for SceneTransition base class."""

    def test_fade_init(self):
        fade = Fade(duration=0.3, easing=easing.in_out)
        assert fade.duration == 0.3
        assert fade.easing == easing.in_out

    def test_invalid_duration_raises(self):
        with pytest.raises(ValueError, match="positive"):
            Fade(duration=0)
        with pytest.raises(ValueError, match="positive"):
            Fade(duration=-0.5)

    def test_repr(self):
        fade = Fade(duration=0.3)
        assert "Fade" in repr(fade)
        assert "0.3" in repr(fade)


@pytest.mark.unit
class TestRenderContext:
    """Tests for RenderContext dataclass."""

    def test_create_render_context(self):
        ctx = RenderContext(width=800, height=600)
        assert ctx.width == 800
        assert ctx.height == 600
        assert ctx.render_scale == 1.0
        assert ctx.origin == "center"

    def test_render_context_with_all_params(self):
        ctx = RenderContext(
            width=1920, height=1080, render_scale=2.0, origin="top-left"
        )
        assert ctx.width == 1920
        assert ctx.height == 1080
        assert ctx.render_scale == 2.0
        assert ctx.origin == "top-left"


# ==============================================================================
# Individual Transition Tests
# ==============================================================================


@pytest.mark.unit
class TestFadeTransition:
    """Tests for Fade transition."""

    def test_fade_composite(self, simple_scene_1, simple_scene_2):
        fade = Fade(duration=0.3)
        ctx = RenderContext(width=400, height=300)

        # Test at different progress values
        for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
            drawing = fade.composite(
                scene_out=simple_scene_1,
                scene_in=simple_scene_2,
                progress=progress,
                time_out=0.5,
                time_in=0.5,
                ctx=ctx,
            )
            assert drawing is not None


@pytest.mark.unit
class TestWipeTransition:
    """Tests for Wipe transition."""

    @pytest.mark.parametrize("direction", ["left", "right", "up", "down"])
    def test_wipe_directions(self, simple_scene_1, simple_scene_2, direction):
        wipe = Wipe(direction=direction, duration=0.3)
        ctx = RenderContext(width=400, height=300)

        drawing = wipe.composite(
            scene_out=simple_scene_1,
            scene_in=simple_scene_2,
            progress=0.5,
            time_out=0.5,
            time_in=0.5,
            ctx=ctx,
        )
        assert drawing is not None

    def test_wipe_repr(self):
        wipe = Wipe(direction="left", duration=0.3)
        assert "Wipe" in repr(wipe)
        assert "left" in repr(wipe)


@pytest.mark.unit
class TestSlideTransition:
    """Tests for Slide transition."""

    @pytest.mark.parametrize("direction", ["left", "right", "up", "down"])
    def test_slide_directions(self, simple_scene_1, simple_scene_2, direction):
        slide = Slide(direction=direction, duration=0.3)
        ctx = RenderContext(width=400, height=300)

        drawing = slide.composite(
            scene_out=simple_scene_1,
            scene_in=simple_scene_2,
            progress=0.5,
            time_out=0.5,
            time_in=0.5,
            ctx=ctx,
        )
        assert drawing is not None

    def test_slide_repr(self):
        slide = Slide(direction="right", duration=0.3)
        assert "Slide" in repr(slide)
        assert "right" in repr(slide)


@pytest.mark.unit
class TestZoomTransition:
    """Tests for Zoom transition."""

    @pytest.mark.parametrize("direction", ["in", "out"])
    def test_zoom_directions(self, simple_scene_1, simple_scene_2, direction):
        zoom = Zoom(direction=direction, duration=0.3)
        ctx = RenderContext(width=400, height=300)

        drawing = zoom.composite(
            scene_out=simple_scene_1,
            scene_in=simple_scene_2,
            progress=0.5,
            time_out=0.5,
            time_in=0.5,
            ctx=ctx,
        )
        assert drawing is not None

    def test_zoom_with_max_scale(self, simple_scene_1, simple_scene_2):
        zoom = Zoom(direction="in", duration=0.3, max_scale=3.0)
        ctx = RenderContext(width=400, height=300)

        drawing = zoom.composite(
            scene_out=simple_scene_1,
            scene_in=simple_scene_2,
            progress=0.5,
            time_out=0.5,
            time_in=0.5,
            ctx=ctx,
        )
        assert drawing is not None

    def test_zoom_repr(self):
        zoom = Zoom(direction="in", duration=0.3)
        assert "Zoom" in repr(zoom)
        assert "in" in repr(zoom)


@pytest.mark.unit
class TestIrisTransition:
    """Tests for Iris transition."""

    @pytest.mark.parametrize("direction", ["open", "close"])
    def test_iris_directions(self, simple_scene_1, simple_scene_2, direction):
        iris = Iris(direction=direction, duration=0.3)
        ctx = RenderContext(width=400, height=300)

        drawing = iris.composite(
            scene_out=simple_scene_1,
            scene_in=simple_scene_2,
            progress=0.5,
            time_out=0.5,
            time_in=0.5,
            ctx=ctx,
        )
        assert drawing is not None

    def test_iris_with_custom_center(self, simple_scene_1, simple_scene_2):
        iris = Iris(direction="open", duration=0.3, center=(100, 100))
        ctx = RenderContext(width=400, height=300)

        drawing = iris.composite(
            scene_out=simple_scene_1,
            scene_in=simple_scene_2,
            progress=0.5,
            time_out=0.5,
            time_in=0.5,
            ctx=ctx,
        )
        assert drawing is not None

    def test_iris_repr(self):
        iris = Iris(direction="open", duration=0.3)
        assert "Iris" in repr(iris)
        assert "open" in repr(iris)


# ==============================================================================
# Time Mapping Tests
# ==============================================================================


@pytest.mark.unit
class TestVSceneSequenceTimeMapping:
    """Tests for time mapping in VSceneSequence."""

    def test_single_scene_full_timeline(self, simple_scene_1):
        seq = VSceneSequence().scene(simple_scene_1, duration=1.0)
        segments = seq._compute_segments()
        assert len(segments) == 1
        assert segments[0].start == 0.0
        assert segments[0].end == 1.0

    def test_two_scenes_with_transition(self, simple_scene_1, simple_scene_2):
        seq = (
            VSceneSequence()
            .scene(simple_scene_1, duration=0.5)
            .transition(Fade(duration=0.2))
            .scene(simple_scene_2, duration=0.3)
        )
        segments = seq._compute_segments()

        # Should have 2 scene segments + 1 transition segment
        scene_segments = [s for s in segments if not s.is_transition]
        trans_segments = [s for s in segments if s.is_transition]

        assert len(scene_segments) == 2
        assert len(trans_segments) == 1

    def test_segments_cover_full_timeline(
        self, simple_scene_1, simple_scene_2, simple_scene_3
    ):
        seq = (
            VSceneSequence()
            .scene(simple_scene_1, duration=0.3)
            .transition(Fade(duration=0.1))
            .scene(simple_scene_2, duration=0.4)
            .transition(Wipe(duration=0.1))
            .scene(simple_scene_3, duration=0.2)
        )
        segments = seq._compute_segments()
        scene_segments = [s for s in segments if not s.is_transition]

        # First segment starts at 0
        assert scene_segments[0].start == pytest.approx(0.0)
        # Last segment ends at 1
        assert scene_segments[-1].end == pytest.approx(1.0)
