"""Tests for VElement chainable builder methods"""

import pytest

from svan2d.component.renderer.circle import CircleRenderer
from svan2d.component.state.circle import CircleState
from svan2d.component.state.rectangle import RectangleState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.transition.curve import bezier, linear
from svan2d.velement import VElement


class TestVElementBuilderBasic:
    """Tests for basic builder functionality"""

    def test_builder_creates_velement(self):
        """Chainable methods should create a valid VElement"""
        state1 = CircleState(radius=50, pos=Point2D(0, 0))
        state2 = CircleState(radius=100, pos=Point2D(100, 100))

        element = VElement().keystate(state1, at=0.0).keystate(state2, at=1.0)

        assert isinstance(element, VElement)
        # Trigger build via get_frame
        element.get_frame(0.0)
        assert len(element._keystates_list) == 2

    def test_builder_renderer(self):
        """Builder should accept a renderer"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)
        renderer = CircleRenderer()

        element = (
            VElement()
            .renderer(renderer)
            .keystate(state1, at=0.0)
            .keystate(state2, at=1.0)
        )

        assert element._renderer is renderer

    def test_builder_minimum_keystates_error(self):
        """Builder should error at render time if no keystates"""
        element = VElement()

        with pytest.raises(ValueError, match="at least 1 keystate"):
            element.render()

    def test_single_keystate_works(self):
        """Single keystate should work for static element"""
        state1 = CircleState(radius=50)
        element = VElement().keystate(state1, at=0.0)

        # Should not raise
        frame = element.get_frame(0.0)
        assert frame is not None
        assert frame.radius == 50


class TestVElementBuilderTransition:
    """Tests for transition configuration"""

    def test_transition_between_keystates(self):
        """Transition should be applied to segment"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)

        element = (
            VElement()
            .keystate(state1, at=0.0)
            .transition(easing_dict={"radius": easing.in_out})
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        # Transition should be attached to first keystate
        assert element._keystates_list[0].transition_config is not None
        assert "radius" in element._keystates_list[0].transition_config.easing_dict

    def test_transition_before_first_keystate_error(self):
        """Transition before first keystate should error"""
        with pytest.raises(ValueError, match="before the first keystate"):
            VElement().transition(easing_dict={"pos": easing.linear})

    def test_transition_after_last_keystate_error(self):
        """Transition after last keystate should error at render"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)

        element = (
            VElement()
            .keystate(state1, at=0.0)
            .keystate(state2, at=1.0)
            .transition(easing_dict={"pos": easing.linear})
        )

        with pytest.raises(ValueError, match="after the last keystate"):
            element.render()

    def test_consecutive_transitions_merge(self):
        """Multiple consecutive transitions should merge"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)

        element = (
            VElement()
            .keystate(state1, at=0.0)
            .transition(easing_dict={"radius": easing.in_out})
            .transition(easing_dict={"opacity": easing.linear})
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        transition = element._keystates_list[0].transition_config
        assert transition is not None
        assert "radius" in transition.easing_dict
        assert "opacity" in transition.easing_dict


class TestVElementBuilderPath:
    """Tests for path configuration"""

    def test_transition_with_path(self):
        """Transition should accept path config"""
        state1 = CircleState(radius=50, pos=Point2D(0, 0))
        state2 = CircleState(radius=50, pos=Point2D(100, 100))

        element = (
            VElement()
            .keystate(state1, at=0.0)
            .transition(interpolation_dict={"pos": bezier([Point2D(0, 100)])})
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        transition = element._keystates_list[0].transition_config
        assert transition is not None
        assert "pos" in transition.interpolation_dict

    def test_path_merging_in_transitions(self):
        """Consecutive transitions should merge paths"""
        state1 = CircleState(radius=50, pos=Point2D(0, 0))
        state2 = CircleState(radius=50, pos=Point2D(100, 100))

        element = (
            VElement()
            .keystate(state1, at=0.0)
            .transition(
                easing_dict={"pos": easing.in_out},
                interpolation_dict={"pos": bezier([Point2D(0, 100)])},
            )
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        transition = element._keystates_list[0].transition_config
        assert transition is not None
        assert "pos" in transition.easing_dict
        assert "pos" in transition.interpolation_dict


class TestVElementBuilderMorphing:
    """Tests for morphing configuration"""

    def test_transition_with_morphing(self):
        """Transition should accept morphing config"""
        from svan2d.transition.mapping import SimpleMapper
        from svan2d.velement import MorphingConfig

        state1 = CircleState(radius=50)
        state2 = RectangleState(width=100, height=100)

        element = (
            VElement()
            .keystate(state1, at=0.0)
            .transition(morphing_config=MorphingConfig(mapper=SimpleMapper()))
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        transition = element._keystates_list[0].transition_config
        assert transition is not None
        assert transition.morphing_config is not None
        assert isinstance(transition.morphing_config, MorphingConfig)

    def test_morphing_overwrite_in_consecutive_transitions(self):
        """Later morphing call should overwrite previous"""
        from svan2d.transition.mapping import (
            GreedyMapper,
            SimpleMapper,
        )
        from svan2d.velement import MorphingConfig

        state1 = CircleState(radius=50)
        state2 = RectangleState(width=100, height=100)

        element = (
            VElement()
            .keystate(state1, at=0.0)
            .transition(morphing_config=MorphingConfig(mapper=SimpleMapper()))
            .transition(morphing_config=MorphingConfig(mapper=GreedyMapper()))
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        transition = element._keystates_list[0].transition_config
        assert transition is not None
        assert isinstance(transition.morphing_config.mapper, GreedyMapper)


class TestVElementBuilderAttributes:
    """Tests for element-level attribute configuration"""

    def test_attributes_easing(self):
        """Attributes should set element-level easing"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)

        element = (
            VElement()
            .attributes(easing_dict={"pos": easing.in_out})
            .keystate(state1, at=0.0)
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        # Check that attribute_easing was passed
        assert element.easing_resolver.attribute_easing is not None
        assert "pos" in element.easing_resolver.attribute_easing

    def test_attributes_path(self):
        """Attributes should set element-level path"""
        state1 = CircleState(radius=50, pos=Point2D(0, 0))
        state2 = CircleState(radius=50, pos=Point2D(100, 100))

        element = (
            VElement()
            .attributes(interpolation_dict={"pos": bezier([Point2D(50, 50)])})
            .keystate(state1, at=0.0)
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        # Element-level path should be merged into each keystate's transition
        assert element._keystates_list[0].transition_config is not None
        assert "pos" in element._keystates_list[0].transition_config.interpolation_dict

    def test_attributes_keystates(self):
        """Attributes should set attribute keystates"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)
        color1 = Color.from_hex("#ff0000")
        color2 = Color.from_hex("#0000ff")

        element = (
            VElement()
            .attributes(keystates_dict={"fill_color": [color1, color2]})
            .keystate(state1, at=0.0)
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        assert "fill_color" in element.attribute_keystates


class TestVElementBuilderClipMask:
    """Tests for clipping and masking"""

    def test_single_clip(self):
        """Single clip should be set"""
        clip_state = CircleState(radius=50)
        clip_element = VElement(state=clip_state)

        state1 = RectangleState(width=100, height=100)
        state2 = RectangleState(width=200, height=200)

        element = (
            VElement()
            .clip(clip_element)
            .keystate(state1, at=0.0)
            .keystate(state2, at=1.0)
        )

        assert clip_element in element.clip_elements

    def test_multiple_clips(self):
        """Multiple clips should accumulate"""
        clip1 = VElement(state=CircleState(radius=50))
        clip2 = VElement(state=CircleState(radius=30))

        state1 = RectangleState(width=100, height=100)
        state2 = RectangleState(width=200, height=200)

        element = (
            VElement()
            .clip(clip1)
            .clip(clip2)
            .keystate(state1, at=0.0)
            .keystate(state2, at=1.0)
        )

        assert len(element.clip_elements) == 2

    def test_mask(self):
        """Mask should be set"""
        mask_state = CircleState(radius=50)
        mask_element = VElement(state=mask_state)

        state1 = RectangleState(width=100, height=100)
        state2 = RectangleState(width=200, height=200)

        element = (
            VElement()
            .mask(mask_element)
            .keystate(state1, at=0.0)
            .keystate(state2, at=1.0)
        )

        assert element.mask_element is mask_element


class TestVElementBuilderAutoTiming:
    """Tests for auto-timing behavior"""

    def test_auto_timing_two_keystates(self):
        """Auto-timing should distribute 2 keystates at 0.0 and 1.0"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)

        element = VElement().keystate(state1).keystate(state2)

        # Trigger build
        element.get_frame(0.0)

        assert element._keystates_list[0].time == 0.0
        assert element._keystates_list[1].time == 1.0

    def test_auto_timing_three_keystates(self):
        """Auto-timing should distribute 3 keystates evenly"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=75)
        state3 = CircleState(radius=100)

        element = VElement().keystate(state1).keystate(state2).keystate(state3)

        # Trigger build
        element.get_frame(0.0)

        assert element._keystates_list[0].time == 0.0
        assert element._keystates_list[1].time == 0.5
        assert element._keystates_list[2].time == 1.0

    def test_mixed_timing(self):
        """Mixed explicit and auto timing should work"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=75)
        state3 = CircleState(radius=100)

        element = (
            VElement()
            .keystate(state1, at=0.0)
            .keystate(state2)  # auto-timed
            .keystate(state3, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        assert element._keystates_list[0].time == 0.0
        assert element._keystates_list[1].time == 0.5
        assert element._keystates_list[2].time == 1.0


class TestVElementBuilderInterpolation:
    """Tests for actual interpolation with builder-created elements"""

    def test_interpolation_works(self):
        """Element created by builder should interpolate correctly"""
        state1 = CircleState(radius=50, pos=Point2D(0, 0))
        state2 = CircleState(radius=100, pos=Point2D(100, 100))

        element = VElement().keystate(state1, at=0.0).keystate(state2, at=1.0)

        # Check interpolation at midpoint
        mid_state = element.get_frame(0.5)
        assert mid_state is not None
        assert mid_state.radius == pytest.approx(75, rel=0.01)
        assert mid_state.pos.x == pytest.approx(50, rel=0.01)
        assert mid_state.pos.y == pytest.approx(50, rel=0.01)

    def test_easing_applied(self):
        """Easing from transition should be applied"""
        state1 = CircleState(radius=0, pos=Point2D(0, 0))
        state2 = CircleState(radius=100, pos=Point2D(100, 0))

        # Use in_out easing which should slow down at endpoints
        element = (
            VElement()
            .keystate(state1, at=0.0)
            .transition(easing_dict={"radius": easing.in_out})
            .keystate(state2, at=1.0)
        )

        # At t=0.5, in_out easing should give roughly 0.5 (symmetric)
        mid_state = element.get_frame(0.5)
        assert mid_state is not None
        # in_out at 0.5 should be approximately 0.5
        assert mid_state.radius == pytest.approx(50, rel=0.1)


class TestVElementBuilderDefaultTransition:
    """Tests for default_transition functionality"""

    def test_default_transition_applies_to_all_segments(self):
        """Default transition should apply to all subsequent segments"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)
        state3 = CircleState(radius=150)

        element = (
            VElement()
            .default_transition(easing_dict={"radius": easing.in_out})
            .keystate(state1, at=0.0)
            .keystate(state2, at=0.5)
            .keystate(state3, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        # Both segments should have the easing
        assert element._keystates_list[0].transition_config is not None
        assert "radius" in element._keystates_list[0].transition_config.easing_dict
        assert element._keystates_list[1].transition_config is not None
        assert "radius" in element._keystates_list[1].transition_config.easing_dict

    def test_default_transition_can_be_changed(self):
        """Default transition can be changed mid-chain"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)
        state3 = CircleState(radius=150)
        state4 = CircleState(radius=200)

        element = (
            VElement()
            .default_transition(easing_dict={"radius": easing.in_out})
            .keystate(state1, at=0.0)
            .keystate(state2, at=0.33)
            .default_transition(easing_dict={"radius": easing.linear})
            .keystate(state3, at=0.66)
            .keystate(state4, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        # First segment: in_out
        assert (
            element._keystates_list[0].transition_config.easing_dict["radius"]
            == easing.in_out
        )
        # Second segment: linear (changed default)
        assert (
            element._keystates_list[1].transition_config.easing_dict["radius"]
            == easing.linear
        )
        # Third segment: linear (still using changed default)
        assert (
            element._keystates_list[2].transition_config.easing_dict["radius"]
            == easing.linear
        )

    def test_explicit_transition_overrides_default(self):
        """Explicit transition() should override default_transition"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)
        state3 = CircleState(radius=150)

        element = (
            VElement()
            .default_transition(easing_dict={"radius": easing.in_out})
            .keystate(state1, at=0.0)
            .transition(easing_dict={"radius": easing.linear})  # explicit override
            .keystate(state2, at=0.5)
            .keystate(state3, at=1.0)  # back to default
        )

        # Trigger build
        element.get_frame(0.0)

        # First segment: explicit linear
        assert (
            element._keystates_list[0].transition_config.easing_dict["radius"]
            == easing.linear
        )
        # Second segment: back to default in_out
        assert (
            element._keystates_list[1].transition_config.easing_dict["radius"]
            == easing.in_out
        )

    def test_default_transition_merges_settings(self):
        """Multiple default_transition calls should merge settings"""
        state1 = CircleState(radius=50, pos=Point2D(0, 0))
        state2 = CircleState(radius=100, pos=Point2D(100, 100))

        element = (
            VElement()
            .default_transition(easing_dict={"radius": easing.in_out})
            .default_transition(easing_dict={"pos": easing.linear})
            .keystate(state1, at=0.0)
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        # Both easings should be present
        transition = element._keystates_list[0].transition_config
        assert "radius" in transition.easing_dict
        assert "pos" in transition.easing_dict
        assert transition.easing_dict["radius"] == easing.in_out
        assert transition.easing_dict["pos"] == easing.linear

    def test_default_transition_with_path(self):
        """Default transition should work with path config"""
        state1 = CircleState(radius=50, pos=Point2D(0, 0))
        state2 = CircleState(radius=50, pos=Point2D(100, 100))
        state3 = CircleState(radius=50, pos=Point2D(200, 0))

        element = (
            VElement()
            .default_transition(interpolation_dict={"pos": bezier([Point2D(50, 50)])})
            .keystate(state1, at=0.0)
            .keystate(state2, at=0.5)
            .keystate(state3, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        # Both segments should have the interpolation_dict
        assert element._keystates_list[0].transition_config is not None
        assert "pos" in element._keystates_list[0].transition_config.interpolation_dict
        assert element._keystates_list[1].transition_config is not None
        assert "pos" in element._keystates_list[1].transition_config.interpolation_dict

    def test_default_transition_before_first_keystate(self):
        """default_transition can be called before first keystate"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)

        # Should not raise
        element = (
            VElement()
            .default_transition(easing_dict={"radius": easing.in_out})
            .keystate(state1, at=0.0)
            .keystate(state2, at=1.0)
        )

        # Trigger build
        element.get_frame(0.0)

        assert element._keystates_list[0].transition_config is not None

    def test_no_default_transition_no_config(self):
        """Without default or explicit transition, no config is attached"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)

        element = VElement().keystate(state1, at=0.0).keystate(state2, at=1.0)

        # Trigger build
        element.get_frame(0.0)

        # No transition config (uses system defaults)
        assert element._keystates_list[0].transition_config is None


class TestVElementConvenienceConstructor:
    """Tests for convenience constructor patterns"""

    def test_state_convenience(self):
        """VElement(state=s) should work"""
        state = CircleState(radius=50)
        element = VElement(state=state)

        frame = element.get_frame(0.0)
        assert frame is not None
        assert frame.radius == 50

    def test_keystates_convenience(self):
        """VElement().keystates([...]) should work"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)

        element = VElement().keystates([state1, state2])

        mid = element.get_frame(0.5)
        assert mid is not None
        assert mid.radius == pytest.approx(75, rel=0.01)

    def test_cannot_modify_after_render(self):
        """Cannot add keystates after rendering"""
        state1 = CircleState(radius=50)
        state2 = CircleState(radius=100)

        element = VElement().keystate(state1).keystate(state2)
        element.render()  # Triggers build

        with pytest.raises(RuntimeError, match="Cannot modify"):
            element.keystate(CircleState(radius=150))
