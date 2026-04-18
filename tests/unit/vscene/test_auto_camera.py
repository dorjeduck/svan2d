"""Tests for scene bounds and auto-camera."""

import sys
from unittest.mock import patch

import pytest

from svan2d.primitive.state.circle import CircleState
from svan2d.core.point2d import Point2D
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.vscene.bounds import scene_bounds_at


@pytest.mark.unit
class TestSceneBoundsAt:
    def test_static_circle(self):
        scene = VScene(width=400, height=300)
        element = VElement(state=CircleState(radius=50))
        scene = scene.add_element(element)

        bounds = scene_bounds_at(scene, 0.5)
        assert bounds is not None
        min_x, min_y, max_x, max_y = bounds
        assert min_x == pytest.approx(-50, abs=1)
        assert max_x == pytest.approx(50, abs=1)

    def test_two_elements_union(self):
        scene = VScene(width=800, height=600)
        e1 = VElement(state=CircleState(radius=10, pos=Point2D(-100, 0)))
        e2 = VElement(state=CircleState(radius=10, pos=Point2D(100, 0)))
        scene = scene.add_elements([e1, e2])

        bounds = scene_bounds_at(scene, 0.0)
        assert bounds is not None
        min_x, _, max_x, _ = bounds
        assert min_x == pytest.approx(-110, abs=1)
        assert max_x == pytest.approx(110, abs=1)

    def test_empty_scene(self):
        scene = VScene(width=400, height=300)
        assert scene_bounds_at(scene, 0.0) is None

    def test_exclude_filter(self):
        scene = VScene(width=800, height=600)
        e1 = VElement(state=CircleState(radius=10, pos=Point2D(-100, 0)))
        e2 = VElement(state=CircleState(radius=10, pos=Point2D(100, 0)))
        scene = scene.add_elements([e1, e2])

        # Exclude e2 — only e1 contributes
        bounds = scene_bounds_at(scene, 0.0, exclude=[e2])
        assert bounds is not None
        min_x, _, max_x, _ = bounds
        assert min_x == pytest.approx(-110, abs=1)
        assert max_x == pytest.approx(-90, abs=1)


@pytest.mark.unit
class TestAutoCamera:
    def test_static_scene_constant_scale(self):
        pytest.importorskip("scipy")
        from svan2d.vscene.automatic_camera import automatic_camera

        scene = VScene(width=400, height=300)
        element = VElement(state=CircleState(radius=50))
        scene = scene.add_element(element)

        result = automatic_camera(scene, padding=1.0)
        assert result is not None
        # Should have camera configured
        assert result._has_camera_funcs()

    def test_with_custom_offset(self):
        pytest.importorskip("scipy")
        from svan2d.vscene.automatic_camera import automatic_camera

        scene = VScene(width=400, height=300)
        element = VElement(state=CircleState(radius=50))
        scene = scene.add_element(element)

        offset_fn = lambda t: Point2D(0.0, 0.0)
        result = automatic_camera(scene, offset=offset_fn)
        assert result is not None
        assert result._has_camera_funcs()

    def test_with_sample_times(self):
        pytest.importorskip("scipy")
        from svan2d.vscene.automatic_camera import automatic_camera

        scene = VScene(width=400, height=300)
        e1 = VElement(state=CircleState(radius=50))
        scene = scene.add_element(e1)

        result = automatic_camera(scene, sample_times=[0.0, 0.25, 0.5, 0.75, 1.0])
        assert result is not None
        assert result._has_camera_funcs()

    def test_sample_times_and_samples_raises(self):
        pytest.importorskip("scipy")
        from svan2d.vscene.automatic_camera import automatic_camera

        scene = VScene(width=400, height=300)
        scene = scene.add_element(VElement(state=CircleState(radius=50)))

        with pytest.raises(ValueError, match="mutually exclusive"):
            automatic_camera(scene, samples=10, sample_times=[0.0, 0.5, 1.0])

    def test_missing_scipy_raises(self):
        with patch.dict(sys.modules, {"scipy": None, "scipy.interpolate": None}):
            # Need to reload the module to pick up the patched import
            import importlib

            import svan2d.vscene.automatic_camera as mod

            importlib.reload(mod)
            with pytest.raises(RuntimeError, match="scipy"):
                mod.automatic_camera(VScene(width=400, height=300), samples=5)

            # Reload again to restore normal state
            importlib.reload(mod)
