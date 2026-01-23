"""Tests for svan2d.vscene.vscene module."""

from unittest.mock import MagicMock, patch

import pytest

from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.vscene import VScene
from svan2d.vscene.camera_state import CameraState


@pytest.mark.unit
class TestVSceneCreation:
    """Tests for VScene initialization."""

    def test_create_with_defaults(self):
        scene = VScene()
        assert scene.width > 0
        assert scene.height > 0
        assert scene.elements == []

    def test_create_with_dimensions(self):
        scene = VScene(width=640, height=480)
        assert scene.width == 640
        assert scene.height == 480

    def test_create_with_background(self):
        scene = VScene(background=Color(255, 0, 0))
        assert scene.background == Color(255, 0, 0)

    def test_create_with_none_background_string(self):
        scene = VScene(background="none")
        assert scene.background is None

    def test_create_with_background_opacity(self):
        scene = VScene(background_opacity=0.5)
        assert scene.background_opacity == 0.5

    def test_create_with_origin_center(self):
        scene = VScene(origin="center")
        assert scene.origin == "center"

    def test_create_with_origin_top_left(self):
        scene = VScene(origin="top-left")
        assert scene.origin == "top-left"

    def test_create_with_transforms(self):
        scene = VScene(offset_x=10, offset_y=20, scale=2.0, rotation=45)
        assert scene.offset_x == 10
        assert scene.offset_y == 20
        assert scene.scale == 2.0
        assert scene.rotation == 45

    def test_invalid_dimensions_raises(self):
        with pytest.raises(ValueError):
            VScene(width=-100, height=100)

    def test_invalid_opacity_raises(self):
        with pytest.raises(ValueError):
            VScene(background_opacity=1.5)


@pytest.mark.unit
class TestVSceneElementManagement:
    """Tests for element management methods."""

    def test_add_element(self):
        scene = VScene()
        mock_element = MagicMock()
        scene.add_element(mock_element)
        assert len(scene.elements) == 1
        assert scene.elements[0] is mock_element

    def test_add_elements(self):
        scene = VScene()
        elements = [MagicMock(), MagicMock(), MagicMock()]
        scene.add_elements(elements)
        assert len(scene.elements) == 3

    def test_remove_element(self):
        scene = VScene()
        element = MagicMock()
        scene.add_element(element)
        result = scene.remove_element(element)
        assert result is True
        assert len(scene.elements) == 0

    def test_remove_element_not_found(self):
        scene = VScene()
        element = MagicMock()
        result = scene.remove_element(element)
        assert result is False

    def test_clear_elements(self):
        scene = VScene()
        scene.add_elements([MagicMock(), MagicMock()])
        scene.clear_elements()
        assert len(scene.elements) == 0

    def test_element_count(self):
        scene = VScene()
        scene.add_elements([MagicMock(), MagicMock()])
        assert scene.element_count() == 2

    def test_animatable_element_count(self):
        scene = VScene()
        animatable = MagicMock()
        animatable.is_animatable.return_value = True
        static = MagicMock()
        static.is_animatable.return_value = False
        scene.add_elements([animatable, static])
        assert scene.animatable_element_count() == 1


@pytest.mark.unit
class TestVSceneProperties:
    """Tests for VScene property accessors."""

    def test_dimensions_property(self):
        scene = VScene(width=800, height=600)
        assert scene.dimensions == (800, 600)

    def test_aspect_ratio_property(self):
        scene = VScene(width=800, height=400)
        assert scene.aspect_ratio == 2.0


@pytest.mark.unit
class TestVSceneRendering:
    """Tests for VScene rendering methods."""

    def test_to_drawing_returns_drawing(self):
        scene = VScene(width=100, height=100)
        drawing = scene.to_drawing(frame_time=0.0)
        assert drawing is not None

    def test_to_drawing_with_background(self):
        scene = VScene(width=100, height=100, background=Color(255, 0, 0))
        drawing = scene.to_drawing(frame_time=0.0)
        assert drawing is not None

    def test_to_drawing_invalid_frame_time_raises(self):
        scene = VScene()
        with pytest.raises(ValueError):
            scene.to_drawing(frame_time=-0.5)
        with pytest.raises(ValueError):
            scene.to_drawing(frame_time=1.5)

    def test_to_svg_returns_string(self):
        scene = VScene(width=100, height=100)
        svg = scene.to_svg(frame_time=0.0)
        assert isinstance(svg, str)
        assert "<svg" in svg

    def test_to_svg_with_elements(self):
        scene = VScene(width=100, height=100)
        element = MagicMock()
        element.get_frame.return_value = MagicMock(z_index=0)
        element.render_state.return_value = None
        scene.add_element(element)
        svg = scene.to_svg(frame_time=0.5)
        assert isinstance(svg, str)
        element.get_frame.assert_called()

    def test_to_drawing_with_render_scale(self):
        scene = VScene(width=100, height=100)
        drawing = scene.to_drawing(frame_time=0.0, render_scale=2.0)
        assert drawing is not None


@pytest.mark.unit
class TestVSceneTransforms:
    """Tests for VScene transform building."""

    def test_build_transform_empty(self):
        scene = VScene()
        transform = scene._build_transform(1.0)
        assert transform == ""

    def test_build_transform_with_scale(self):
        scene = VScene(scale=2.0)
        transform = scene._build_transform(1.0)
        assert "scale(2.0)" in transform

    def test_build_transform_with_rotation(self):
        scene = VScene(rotation=45)
        transform = scene._build_transform(1.0)
        assert "rotate(45)" in transform

    def test_build_transform_with_offset(self):
        scene = VScene(offset_x=10, offset_y=20)
        transform = scene._build_transform(1.0)
        assert "translate(10,20)" in transform

    def test_build_transform_combined(self):
        scene = VScene(scale=2.0, rotation=45, offset_x=10, offset_y=20)
        transform = scene._build_transform(1.0)
        assert "scale" in transform
        assert "rotate" in transform
        assert "translate" in transform


@pytest.mark.unit
class TestVSceneCameraAnimation:
    """Tests for camera animation methods."""

    def test_camera_keystate(self):
        scene = VScene()
        state = CameraState(scale=1.0)
        result = scene.camera_keystate(state, at=0.0)
        assert result is scene  # Returns self for chaining
        assert len(scene._camera_keystates) == 1

    def test_camera_transition_without_keystate_raises(self):
        scene = VScene()
        with pytest.raises(ValueError):
            scene.camera_transition()

    def test_animate_camera_creates_keystates(self):
        scene = VScene()
        scene.animate_camera(scale=(1.0, 2.0))
        assert len(scene._camera_keystates) == 2

    def test_animate_camera_with_offset(self):
        scene = VScene()
        scene.animate_camera(offset=((0, 0), (100, 100)))
        assert len(scene._camera_keystates) == 2

    def test_animate_camera_with_rotation(self):
        scene = VScene()
        scene.animate_camera(rotation=(0, 360))
        assert len(scene._camera_keystates) == 2

    def test_get_camera_state_no_keystates(self):
        scene = VScene(scale=2.0, offset_x=10, offset_y=20, rotation=45)
        state = scene._get_camera_state_at_time(0.5)
        assert state.scale == 2.0
        assert state.pos.x == 10
        assert state.pos.y == 20

    def test_get_camera_state_with_keystates(self):
        scene = VScene()
        scene.animate_camera(scale=(1.0, 2.0))
        state = scene._get_camera_state_at_time(0.5)
        assert 1.0 <= state.scale <= 2.0


@pytest.mark.unit
class TestVSceneTimelineEasing:
    """Tests for timeline easing."""

    def test_timeline_easing_applied(self):
        def ease_half(t):
            return t * 0.5  # Compress timeline

        scene = VScene(timeline_easing=ease_half)
        element = MagicMock()
        element.get_frame.return_value = MagicMock(z_index=0)
        element.render_state.return_value = None
        scene.add_element(element)

        # At frame_time=1.0, with easing, should call get_frame with 0.5
        scene.to_drawing(frame_time=1.0)
        element.get_frame.assert_called()


@pytest.mark.unit
class TestVSceneAnimationTimeRange:
    """Tests for animation time range calculation."""

    def test_empty_scene_time_range(self):
        scene = VScene()
        min_t, max_t = scene.get_animation_time_range()
        assert min_t == 0.0
        assert max_t == 1.0

    def test_scene_with_keystates_time_range(self):
        scene = VScene()
        element = MagicMock()
        keystate1 = MagicMock()
        keystate1.time = 0.2
        keystate2 = MagicMock()
        keystate2.time = 0.8
        element._keystates_list = [keystate1, keystate2]
        scene.add_element(element)

        min_t, max_t = scene.get_animation_time_range()
        assert min_t == 0.2
        assert max_t == 0.8


@pytest.mark.unit
class TestVSceneRepr:
    """Tests for VScene string representation."""

    def test_repr(self):
        scene = VScene(width=800, height=600)
        repr_str = repr(scene)
        assert "VScene" in repr_str
        assert "800" in repr_str
        assert "600" in repr_str
