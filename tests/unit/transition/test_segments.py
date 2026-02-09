"""Tests for transition segment functions."""

import pytest

from svan2d.component.state.circle import CircleState
from svan2d.component.state.rectangle import RectangleState
from svan2d.core.color import Color, RED, BLUE
from svan2d.core.point2d import Point2D
from svan2d.transition.segment.hold import hold
from svan2d.transition.segment.bounce import bounce
from svan2d.transition.segment.crossfade import crossfade
from svan2d.transition.segment.swap_positions import swap_positions
from svan2d.transition.segment.fade_inout import fade_inout
from svan2d.transition.segment.slide_hold_slide import slide_hold_slide
from svan2d.transition.segment.arc_swap_positions import arc_swap_positions
from svan2d.transition.segment.slide_effect import SlideEffect
from svan2d.transition.easing import in_out


@pytest.fixture
def circle_state():
    return CircleState(pos=Point2D(0, 0), radius=50, fill_color=RED)


@pytest.fixture
def circle_state_2():
    return CircleState(pos=Point2D(100, 100), radius=30, fill_color=BLUE)


@pytest.fixture
def rect_state():
    return RectangleState(pos=Point2D(50, 50), width=100, height=60)


class TestHold:
    """Tests for hold() segment function."""

    def test_hold_single_state_defaults(self, circle_state):
        """Single state with default at and duration."""
        result = hold(circle_state)
        assert len(result) == 2
        assert result[0].state == circle_state
        assert result[1].state == circle_state
        # Default at=0.5, duration=1/3, so times are ~0.33 and ~0.67
        assert result[0].time == pytest.approx(0.5 - 1 / 6, abs=0.01)
        assert result[1].time == pytest.approx(0.5 + 1 / 6, abs=0.01)

    def test_hold_single_state_custom_at(self, circle_state):
        """Single state with custom at time."""
        result = hold(circle_state, at=0.8, hold_duration=0.1)
        assert len(result) == 2
        assert result[0].time == pytest.approx(0.75, abs=0.01)
        assert result[1].time == pytest.approx(0.85, abs=0.01)

    def test_hold_single_state_clamped_to_bounds(self, circle_state):
        """Times should be clamped to [0, 1]."""
        result = hold(circle_state, at=0.0, hold_duration=0.2)
        assert result[0].time == 0.0  # Clamped from -0.1
        assert result[1].time == pytest.approx(0.1, abs=0.01)

    def test_hold_multiple_states(self, circle_state, rect_state):
        """Multiple states with list of times."""
        states = [circle_state, rect_state]
        result = hold(states, at=[0.25, 0.75], hold_duration=0.1)
        assert len(result) == 4  # 2 keystates per state
        assert result[0].state == circle_state
        assert result[2].state == rect_state

    def test_hold_multiple_states_default_times(self, circle_state, rect_state):
        """Multiple states use linspace for default times."""
        states = [circle_state, rect_state]
        result = hold(states)
        assert len(result) == 4

    def test_hold_single_state_list_at_raises(self, circle_state):
        """Single state with list 'at' should raise."""
        with pytest.raises(ValueError, match="must be float"):
            hold(circle_state, at=[0.5])

    def test_hold_list_states_float_at_raises(self, circle_state, rect_state):
        """List of states with float 'at' should raise."""
        with pytest.raises(ValueError, match="must be a list"):
            hold([circle_state, rect_state], at=0.5)

    def test_hold_mismatched_lengths_raises(self, circle_state, rect_state):
        """Mismatched states and times lengths should raise."""
        with pytest.raises(ValueError, match="Length of"):
            hold([circle_state, rect_state], at=[0.5])


class TestBounce:
    """Tests for bounce() segment function."""

    def test_bounce_basic(self, circle_state, circle_state_2):
        """Basic bounce between two states."""
        result = bounce(
            circle_state, circle_state_2, t_start=0.0, t_end=1.0, num_transitions=2
        )
        assert len(result) == 3  # s1 -> s2 -> s1
        assert result[0].state == circle_state
        assert result[1].state == circle_state_2
        assert result[2].state == circle_state

    def test_bounce_times(self, circle_state, circle_state_2):
        """Bounce times are evenly distributed."""
        result = bounce(
            circle_state, circle_state_2, t_start=0.2, t_end=0.8, num_transitions=2
        )
        assert result[0].time == 0.2
        assert result[2].time == 0.8

    def test_bounce_with_hold(self, circle_state, circle_state_2):
        """Bounce with hold duration creates extra keystates."""
        result = bounce(
            circle_state,
            circle_state_2,
            t_start=0.0,
            t_end=1.0,
            num_transitions=2,
            hold_duration=0.1,
        )
        # With hold, intermediate states get 2 keystates each
        assert len(result) > 3

    def test_bounce_num_transitions_3(self, circle_state, circle_state_2):
        """Three transitions: s1 -> s2 -> s1 -> s2."""
        result = bounce(
            circle_state, circle_state_2, t_start=0.0, t_end=1.0, num_transitions=3
        )
        assert len(result) == 4
        assert result[0].state == circle_state
        assert result[1].state == circle_state_2
        assert result[2].state == circle_state
        assert result[3].state == circle_state_2

    def test_bounce_with_easing(self, circle_state, circle_state_2):
        """Bounce with easing dict."""
        easing = {"pos": in_out}
        result = bounce(
            circle_state,
            circle_state_2,
            t_start=0.0,
            t_end=1.0,
            num_transitions=2,
            easing=easing,
        )
        assert result[0].transition_config is not None

    def test_bounce_invalid_hold_raises(self, circle_state, circle_state_2):
        """Hold duration too large should raise."""
        with pytest.raises(ValueError, match="hold durations"):
            bounce(
                circle_state,
                circle_state_2,
                t_start=0.0,
                t_end=0.1,
                num_transitions=2,
                hold_duration=0.5,  # Too large
            )


class TestCrossfade:
    """Tests for crossfade() segment function."""

    def test_crossfade_basic(self, circle_state, rect_state):
        """Basic crossfade between two states."""
        ks_out, ks_in = crossfade(circle_state, rect_state, t_start=0.2, t_end=0.8)

        assert len(ks_out) == 2
        assert len(ks_in) == 2

        # Out element starts visible, ends invisible
        assert ks_out[0].state.opacity == circle_state.opacity
        assert ks_out[1].state.opacity == 0.0

        # In element starts invisible, ends visible
        assert ks_in[0].state.opacity == 0.0
        assert ks_in[1].state.opacity == rect_state.opacity

    def test_crossfade_times(self, circle_state, rect_state):
        """Crossfade times are correct."""
        ks_out, ks_in = crossfade(circle_state, rect_state, t_start=0.3, t_end=0.7)

        assert ks_out[0].time == 0.3
        assert ks_out[1].time == 0.7
        assert ks_in[0].time == 0.3
        assert ks_in[1].time == 0.7

    def test_crossfade_with_delay(self, circle_state, rect_state):
        """Crossfade with delay offsets the in/out times."""
        ks_out, ks_in = crossfade(
            circle_state, rect_state, t_start=0.2, t_end=0.8, delay=0.1
        )

        # Out ends earlier, in starts later
        assert ks_out[1].time == pytest.approx(0.7, abs=0.01)
        assert ks_in[0].time == pytest.approx(0.3, abs=0.01)

    def test_crossfade_preserves_other_properties(self, circle_state, rect_state):
        """Crossfade preserves non-opacity properties."""
        ks_out, ks_in = crossfade(circle_state, rect_state, t_start=0.0, t_end=1.0)

        assert ks_out[0].state.pos == circle_state.pos
        assert ks_in[1].state.pos == rect_state.pos


class TestSwapPositions:
    """Tests for swap_positions() segment function."""

    def test_swap_basic(self, circle_state, circle_state_2):
        """Basic position swap."""
        ks1, ks2 = swap_positions(circle_state, circle_state_2, t_start=0.0, t_end=1.0)

        assert len(ks1) == 2
        assert len(ks2) == 2

        # First element ends at second element's position
        assert ks1[0].state.pos == circle_state.pos
        assert ks1[1].state.pos == circle_state_2.pos

        # Second element ends at first element's position
        assert ks2[0].state.pos == circle_state_2.pos
        assert ks2[1].state.pos == circle_state.pos

    def test_swap_times(self, circle_state, circle_state_2):
        """Swap times are correct."""
        ks1, ks2 = swap_positions(circle_state, circle_state_2, t_start=0.2, t_end=0.8)

        assert ks1[0].time == 0.2
        assert ks1[1].time == 0.8
        assert ks2[0].time == 0.2
        assert ks2[1].time == 0.8

    def test_swap_with_easing(self, circle_state, circle_state_2):
        """Swap with easing dict."""
        easing = {"pos": in_out}
        ks1, ks2 = swap_positions(
            circle_state, circle_state_2, t_start=0.0, t_end=1.0, easing=easing
        )

        assert ks1[0].transition_config is not None
        assert ks2[0].transition_config is not None

    def test_swap_preserves_other_properties(self, circle_state, circle_state_2):
        """Swap preserves non-position properties."""
        ks1, ks2 = swap_positions(circle_state, circle_state_2, t_start=0.0, t_end=1.0)

        # Colors and radii should be preserved
        assert ks1[1].state.fill_color == circle_state.fill_color
        assert ks1[1].state.radius == circle_state.radius
        assert ks2[1].state.fill_color == circle_state_2.fill_color
        assert ks2[1].state.radius == circle_state_2.radius


class TestFadeInOut:
    """Tests for fade_inout() segment function."""

    def test_fade_inout_single_state(self, circle_state):
        """Single state fade in/out."""
        result = fade_inout(circle_state)
        # Should have keystates for: invisible -> visible -> visible -> invisible
        assert len(result) >= 2
        # First keystate should be invisible
        assert result[0].state.opacity == 0
        # Middle should be visible
        assert any(ks.state.opacity == circle_state.opacity for ks in result)

    def test_fade_inout_custom_times(self, circle_state):
        """Custom center time and durations."""
        result = fade_inout(
            circle_state, center_t=0.5, hold_duration=0.2, fade_duration=0.1
        )
        assert len(result) >= 2

    def test_fade_inout_multiple_states(self, circle_state, rect_state):
        """Multiple states with default times."""
        result = fade_inout([circle_state, rect_state])
        assert len(result) >= 4  # At least 2 per state

    def test_fade_inout_multiple_states_custom_times(self, circle_state, rect_state):
        """Multiple states with custom times."""
        result = fade_inout(
            [circle_state, rect_state],
            center_t=[0.25, 0.75],
            hold_duration=0.1,
            fade_duration=0.05,
        )
        assert len(result) >= 4

    def test_fade_inout_single_state_list_at_raises(self, circle_state):
        """Single state with list center_t should raise."""
        with pytest.raises(ValueError, match="must be float"):
            fade_inout(circle_state, center_t=[0.5])

    def test_fade_inout_list_states_float_at_raises(self, circle_state, rect_state):
        """List of states with float center_t should raise."""
        with pytest.raises(ValueError, match="must be a list"):
            fade_inout([circle_state, rect_state], center_t=0.5)


class TestSlideHoldSlide:
    """Tests for slide_hold_slide() segment function."""

    def test_slide_single_state(self, circle_state):
        """Single state slide in, hold, slide out."""
        result = slide_hold_slide(
            circle_state, t_start=0.0, t_end=1.0, slide_duration=0.1
        )
        assert len(result) == 4  # entrance, hold start, hold end, exit
        assert result[0].time == 0.0
        assert result[-1].time == pytest.approx(1.0, abs=0.01)

    def test_slide_entrance_exit_points(self, circle_state):
        """Custom entrance and exit points."""
        entrance = Point2D(200, 0)
        exit_pt = Point2D(-200, 0)
        result = slide_hold_slide(
            circle_state,
            t_start=0.0,
            t_end=1.0,
            entrance_point=entrance,
            exit_point=exit_pt,
        )
        # First state should be at entrance point
        assert result[0].state.pos == entrance
        # Last state should be at exit point
        assert result[-1].state.pos == exit_pt

    def test_slide_with_fade_effect(self, circle_state):
        """Slide with fade effect."""
        result = slide_hold_slide(
            circle_state,
            t_start=0.0,
            t_end=1.0,
            entrance_effect=SlideEffect.FADE,
            exit_effect=SlideEffect.FADE,
        )
        # Entrance and exit states should have opacity=0
        assert result[0].state.opacity == 0
        assert result[-1].state.opacity == 0

    def test_slide_with_scale_effect(self, circle_state):
        """Slide with scale effect."""
        result = slide_hold_slide(
            circle_state,
            t_start=0.0,
            t_end=1.0,
            entrance_effect=SlideEffect.SCALE,
            exit_effect=SlideEffect.SCALE,
        )
        assert result[0].state.scale == 0
        assert result[-1].state.scale == 0

    def test_slide_multiple_states(self, circle_state, rect_state):
        """Multiple states slide in sequence."""
        result = slide_hold_slide(
            [circle_state, rect_state], t_start=0.0, t_end=1.0, slide_duration=0.1
        )
        # Returns list of keystate lists
        assert len(result) == 2
        assert len(result[0]) == 4
        assert len(result[1]) == 4


class TestArcSwapPositions:
    """Tests for arc_swap_positions() segment function."""

    def test_arc_swap_basic(self, circle_state, circle_state_2):
        """Basic arc swap."""
        ks1, ks2 = arc_swap_positions(
            circle_state, circle_state_2, t_start=0.0, t_end=1.0
        )
        assert len(ks1) == 2
        assert len(ks2) == 2
        # Positions should be swapped
        assert ks1[1].state.pos == circle_state_2.pos
        assert ks2[1].state.pos == circle_state.pos

    def test_arc_swap_has_curve(self, circle_state, circle_state_2):
        """Arc swap should have curve in transition config."""
        ks1, ks2 = arc_swap_positions(
            circle_state, circle_state_2, t_start=0.0, t_end=1.0
        )
        assert ks1[0].transition_config is not None
        assert ks1[0].transition_config.interpolation_dict is not None
        assert "pos" in ks1[0].transition_config.interpolation_dict

    def test_arc_swap_clockwise(self, circle_state, circle_state_2):
        """Clockwise arc swap."""
        ks1, _ = arc_swap_positions(
            circle_state, circle_state_2, t_start=0.0, t_end=1.0, clockwise=True
        )
        assert ks1[0].transition_config is not None

    def test_arc_swap_counterclockwise(self, circle_state, circle_state_2):
        """Counter-clockwise arc swap."""
        ks1, _ = arc_swap_positions(
            circle_state, circle_state_2, t_start=0.0, t_end=1.0, clockwise=False
        )
        assert ks1[0].transition_config is not None

    def test_arc_swap_custom_radius(self, circle_state, circle_state_2):
        """Arc swap with custom radius."""
        ks1, ks2 = arc_swap_positions(
            circle_state, circle_state_2, t_start=0.0, t_end=1.0, arc_radius=200
        )
        assert len(ks1) == 2
        assert len(ks2) == 2


class TestSlideEffect:
    """Tests for SlideEffect enum."""

    def test_slide_effect_values(self):
        """SlideEffect has expected values."""
        assert SlideEffect.NONE.value == "none"
        assert SlideEffect.FADE.value == "fade"
        assert SlideEffect.SCALE.value == "scale"
        assert SlideEffect.FADE_SCALE.value == "fade_scale"
