"""Tests for VSceneComposite - spatial composition of scenes."""

import pytest

from svan2d.core import Color
from svan2d.vscene import VScene, VSceneComposite, VSceneSequence


@pytest.fixture
def scene_small():
    """Small scene 100x100."""
    return VScene(width=100, height=100, background=Color("#FF0000"))


@pytest.fixture
def scene_medium():
    """Medium scene 200x150."""
    return VScene(width=200, height=150, background=Color("#00FF00"))


@pytest.fixture
def scene_tall():
    """Tall scene 100x200."""
    return VScene(width=100, height=200, background=Color("#0000FF"))


class TestVSceneCompositeInit:
    """Test VSceneComposite initialization."""

    def test_init_horizontal(self, scene_small, scene_medium):
        comp = VSceneComposite([scene_small, scene_medium], direction="horizontal")
        assert comp.direction == "horizontal"
        assert len(comp.scenes) == 2

    def test_init_vertical(self, scene_small, scene_medium):
        comp = VSceneComposite([scene_small, scene_medium], direction="vertical")
        assert comp.direction == "vertical"

    def test_init_with_gap(self, scene_small, scene_medium):
        comp = VSceneComposite([scene_small, scene_medium], gap=10)
        assert comp.gap == 10

    def test_init_with_origin_override(self, scene_small):
        comp = VSceneComposite([scene_small], origin="top-left")
        assert comp.origin == "top-left"

    def test_init_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            VSceneComposite([])

    def test_init_invalid_direction_raises(self, scene_small):
        with pytest.raises(ValueError, match="direction"):
            VSceneComposite([scene_small], direction="diagonal")  # type: ignore


class TestHorizontalComposite:
    """Test horizontal composition."""

    def test_height_matches_max(self, scene_small, scene_tall):
        """Horizontal composite height should match max scene height."""
        comp = VSceneComposite([scene_small, scene_tall], direction="horizontal")
        assert comp.height == 200  # scene_tall height

    def test_width_is_sum_of_scaled(self, scene_small, scene_tall):
        """Width should be sum of scaled widths."""
        comp = VSceneComposite([scene_small, scene_tall], direction="horizontal")
        # scene_small: 100x100, scaled to height 200 -> scale=2.0 -> width=200
        # scene_tall: 100x200, already at height 200 -> scale=1.0 -> width=100
        assert comp.width == 300

    def test_width_with_gap(self):
        """Width should include gaps between scenes."""
        s1 = VScene(width=100, height=100)
        s2 = VScene(width=100, height=100)
        comp = VSceneComposite([s1, s2], direction="horizontal", gap=20)
        # Both 100x100, no scaling needed, gap=20
        assert comp.width == 220


class TestVerticalComposite:
    """Test vertical composition."""

    def test_width_matches_max(self, scene_small, scene_medium):
        """Vertical composite width should match max scene width."""
        comp = VSceneComposite([scene_small, scene_medium], direction="vertical")
        assert comp.width == 200  # scene_medium width

    def test_height_is_sum_of_scaled(self, scene_small, scene_medium):
        """Height should be sum of scaled heights."""
        comp = VSceneComposite([scene_small, scene_medium], direction="vertical")
        # scene_small: 100x100, scaled to width 200 -> scale=2.0 -> height=200
        # scene_medium: 200x150, already at width 200 -> scale=1.0 -> height=150
        assert comp.height == 350


class TestNestedComposites:
    """Test nesting composites."""

    def test_nested_horizontal_in_vertical(self, scene_small):
        """Test row1, row2 stacked vertically."""
        row1 = VSceneComposite([scene_small, scene_small], direction="horizontal")
        row2 = VSceneComposite([scene_small, scene_small], direction="horizontal")
        grid = VSceneComposite([row1, row2], direction="vertical")

        # Each row is 200x100
        assert row1.width == 200
        assert row1.height == 100

        # Grid stacks two rows
        assert grid.width == 200
        assert grid.height == 200

    def test_nested_vertical_in_horizontal(self, scene_small):
        """Test col1, col2 stacked horizontally."""
        col1 = VSceneComposite([scene_small, scene_small], direction="vertical")
        col2 = VSceneComposite([scene_small, scene_small], direction="vertical")
        grid = VSceneComposite([col1, col2], direction="horizontal")

        # Each col is 100x200
        assert col1.width == 100
        assert col1.height == 200

        # Grid stacks two columns
        assert grid.width == 200
        assert grid.height == 200


class TestOriginHandling:
    """Test origin mode handling."""

    def test_inherits_first_scene_origin(self):
        scene_center = VScene(width=100, height=100, origin="center")
        scene_topleft = VScene(width=100, height=100, origin="top-left")

        comp1 = VSceneComposite([scene_center, scene_topleft])
        assert comp1.origin == "center"

        comp2 = VSceneComposite([scene_topleft, scene_center])
        assert comp2.origin == "top-left"

    def test_origin_override(self):
        scene = VScene(width=100, height=100, origin="center")
        comp = VSceneComposite([scene], origin="top-left")
        assert comp.origin == "top-left"


class TestRendering:
    """Test rendering to drawing and SVG."""

    def test_to_drawing_returns_drawing(self, scene_small, scene_medium):
        comp = VSceneComposite([scene_small, scene_medium])
        drawing = comp.to_drawing(frame_time=0.5)
        assert drawing is not None
        # Check correct dimensions
        assert drawing.width == comp.width
        assert drawing.height == comp.height

    def test_to_svg_returns_string(self, scene_small):
        comp = VSceneComposite([scene_small])
        svg = comp.to_svg(frame_time=0.0, log=False)
        assert isinstance(svg, str)
        assert "<svg" in svg

    def test_invalid_frame_time_raises(self, scene_small):
        comp = VSceneComposite([scene_small])
        with pytest.raises(ValueError, match="frame_time"):
            comp.to_drawing(frame_time=1.5)

    def test_render_scale_applied(self, scene_small):
        comp = VSceneComposite([scene_small])
        drawing = comp.to_drawing(render_scale=2.0)
        assert drawing.width == 200
        assert drawing.height == 200


class TestWithVSceneSequence:
    """Test composites containing VSceneSequence."""

    def test_composite_with_sequence(self, scene_small, scene_medium):
        from svan2d.transition.scene import Fade

        seq = (
            VSceneSequence()
            .scene(scene_small, duration=0.5)
            .transition(Fade(duration=0.1))
            .scene(scene_medium, duration=0.5)
        )

        # Composite containing a sequence
        comp = VSceneComposite([scene_small, seq], direction="horizontal")

        # Should render without error
        drawing = comp.to_drawing(frame_time=0.5)
        assert drawing is not None


class TestRepr:
    """Test string representation."""

    def test_repr(self, scene_small, scene_medium):
        comp = VSceneComposite([scene_small, scene_medium], direction="horizontal")
        r = repr(comp)
        assert "VSceneComposite" in r
        assert "scenes=2" in r
        assert "horizontal" in r
