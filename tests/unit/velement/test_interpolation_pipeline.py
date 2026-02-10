"""Tests for the interpolation pipeline — caching, custom functions, easing priority,
attribute keystates, dual-state keystates, skip-identical optimization, and
the changed-fields cache."""

import pytest

from svan2d.component.state.circle import CircleState
from svan2d.component.state.rectangle import RectangleState
from svan2d.component.state.star import StarState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.transition import easing
from svan2d.transition.easing_resolver import EasingResolver
from svan2d.transition.interpolation_engine import InterpolationEngine
from svan2d.velement import VElement
from svan2d.velement.transition import TransitionConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    """Bare interpolation engine with linear easing."""
    return InterpolationEngine(EasingResolver(attribute_easing_dict={}))


# ---------------------------------------------------------------------------
# 1. Changed-fields cache
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestChangedFieldsCache:
    """Verify that the per-segment changed-fields cache works correctly."""

    def test_cache_populated_after_first_frame(self):
        """Cache should contain an entry for segment 0 after the first frame."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        s2 = CircleState(pos=Point2D(100, 0), radius=50)
        elem = VElement().keystate(s1, at=0.0).keystate(s2, at=1.0)

        elem.get_frame(0.5)

        cache = elem._interpolator._changed_fields_cache
        assert 0 in cache
        changed_names, field_values = cache[0]
        assert "pos" in changed_names
        # radius is the same → must NOT appear in changed set
        assert "radius" not in changed_names

    def test_cache_reused_across_frames(self):
        """Second call should reuse the same cache object (no recomputation)."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        s2 = CircleState(pos=Point2D(100, 0), radius=100)
        elem = VElement().keystate(s1, at=0.0).keystate(s2, at=1.0)

        elem.get_frame(0.3)
        cache_after_first = elem._interpolator._changed_fields_cache[0]

        elem.get_frame(0.7)
        cache_after_second = elem._interpolator._changed_fields_cache[0]

        assert cache_after_first is cache_after_second

    def test_multi_segment_independent_caches(self):
        """Each segment should have its own cache entry."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        s2 = CircleState(pos=Point2D(100, 0), radius=50)
        s3 = CircleState(pos=Point2D(100, 0), radius=100)
        elem = (
            VElement()
            .keystate(s1, at=0.0)
            .keystate(s2, at=0.5)
            .keystate(s3, at=1.0)
        )

        elem.get_frame(0.25)  # segment 0
        elem.get_frame(0.75)  # segment 1

        cache = elem._interpolator._changed_fields_cache
        assert 0 in cache and 1 in cache

        # Segment 0: only pos changes
        assert "pos" in cache[0][0]
        assert "radius" not in cache[0][0]

        # Segment 1: only radius changes
        assert "radius" in cache[1][0]
        assert "pos" not in cache[1][0]


# ---------------------------------------------------------------------------
# 2. Custom interpolation functions (interpolation_dict)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCustomInterpolationFunctions:
    """Verify that interpolation_dict custom functions are called."""

    def test_custom_pos_curve(self):
        """A custom curve should override default pos interpolation."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        s2 = CircleState(pos=Point2D(100, 0), radius=50)

        # Custom curve that always returns a fixed point regardless of t
        def fixed_curve(p1, p2, t):
            return Point2D(42, 42)

        elem = (
            VElement()
            .keystate(s1, at=0.0)
            .transition(interpolation_dict={"pos": fixed_curve})
            .keystate(s2, at=1.0)
        )

        result = elem.get_frame(0.5)
        assert result.pos.x == pytest.approx(42)
        assert result.pos.y == pytest.approx(42)

    def test_custom_function_called_even_when_values_equal(self):
        """Custom interpolation must fire even if start == end value."""
        s1 = CircleState(pos=Point2D(50, 50), radius=50)
        s2 = CircleState(pos=Point2D(50, 50), radius=50)

        call_log = []

        def tracking_curve(p1, p2, t):
            call_log.append(t)
            return Point2D(99, 99)

        elem = (
            VElement()
            .keystate(s1, at=0.0)
            .transition(interpolation_dict={"pos": tracking_curve})
            .keystate(s2, at=1.0)
        )

        result = elem.get_frame(0.5)
        assert len(call_log) > 0
        assert result.pos.x == pytest.approx(99)

    def test_custom_rotation_function(self):
        """A custom rotation function should override angle wrapping."""
        s1 = RectangleState(pos=Point2D(), width=100, height=50, rotation=0)
        s2 = RectangleState(pos=Point2D(), width=100, height=50, rotation=0)

        def spin(r1, r2, t):
            return 720 * t  # Two full revolutions

        elem = (
            VElement()
            .keystate(s1, at=0.0)
            .transition(interpolation_dict={"rotation": spin})
            .keystate(s2, at=1.0)
        )

        result = elem.get_frame(0.5)
        assert result.rotation == pytest.approx(360)

    def test_element_level_interpolation_dict_merged(self):
        """Element-level interpolation_dict should apply to all segments."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        s2 = CircleState(pos=Point2D(100, 0), radius=50)
        s3 = CircleState(pos=Point2D(200, 0), radius=50)

        def always_zero(p1, p2, t):
            return Point2D(0, 0)

        elem = (
            VElement()
            .attributes(interpolation_dict={"pos": always_zero})
            .keystate(s1, at=0.0)
            .keystate(s2, at=0.5)
            .keystate(s3, at=1.0)
        )

        r1 = elem.get_frame(0.25)
        r2 = elem.get_frame(0.75)
        assert r1.pos.x == pytest.approx(0)
        assert r2.pos.x == pytest.approx(0)

    def test_segment_interpolation_overrides_element(self):
        """Segment-level interpolation_dict should take precedence over element-level."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        s2 = CircleState(pos=Point2D(100, 0), radius=50)

        def elem_curve(p1, p2, t):
            return Point2D(-1, -1)

        def seg_curve(p1, p2, t):
            return Point2D(77, 77)

        elem = (
            VElement()
            .attributes(interpolation_dict={"pos": elem_curve})
            .keystate(s1, at=0.0)
            .transition(interpolation_dict={"pos": seg_curve})
            .keystate(s2, at=1.0)
        )

        result = elem.get_frame(0.5)
        assert result.pos.x == pytest.approx(77)


# ---------------------------------------------------------------------------
# 3. linear_angle_interpolation
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLinearAngleInterpolation:
    """Verify that linear_angle_interpolation disables angle wrapping."""

    def test_multi_revolution_with_flag(self):
        """Rotation should go beyond 360 when linear_angle_interpolation=True."""
        s1 = RectangleState(pos=Point2D(), width=100, height=50, rotation=0)
        s2 = RectangleState(pos=Point2D(), width=100, height=50, rotation=720)

        elem = (
            VElement()
            .keystate(s1, at=0.0)
            .transition(linear_angle_interpolation=True)
            .keystate(s2, at=1.0)
        )

        result = elem.get_frame(0.5)
        assert result.rotation == pytest.approx(360)

    def test_angle_wrapping_default(self):
        """Without the flag, rotation should wrap via shortest path."""
        s1 = RectangleState(pos=Point2D(), width=100, height=50, rotation=0)
        s2 = RectangleState(pos=Point2D(), width=100, height=50, rotation=350)

        elem = (
            VElement()
            .keystate(s1, at=0.0)
            .keystate(s2, at=1.0)
        )

        # Default: shortest path from 0 → 350 goes -10 degrees
        result = elem.get_frame(0.5)
        # Shortest path: 0 → 350 wraps to 0 → -10, midpoint is -5
        assert result.rotation == pytest.approx(-5, abs=1)

    def test_linear_angle_interpolation_preserved_with_element_interpolation_dict(self):
        """linear_angle_interpolation should survive merge with element-level interpolation_dict."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50, rotation=0)
        s2 = CircleState(pos=Point2D(100, 0), radius=50, rotation=720)

        def my_curve(p1, p2, t):
            return Point2D(t * 100, 0)

        elem = (
            VElement()
            .attributes(interpolation_dict={"pos": my_curve})
            .keystate(s1, at=0.0)
            .transition(linear_angle_interpolation=True)
            .keystate(s2, at=1.0)
        )

        result = elem.get_frame(0.5)
        assert result.rotation == pytest.approx(360)


# ---------------------------------------------------------------------------
# 4. Easing priority levels
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEasingPriority:
    """Verify the 4-level easing priority system."""

    def test_segment_easing_overrides_element(self):
        """Segment easing_dict should take priority over element attribute_easing."""
        s1 = CircleState(pos=Point2D(0, 0), radius=0)
        s2 = CircleState(pos=Point2D(0, 0), radius=100)

        # Element-level: in_out (should be overridden)
        # Segment-level: step easing (0 until 0.5, then 1)
        elem = (
            VElement()
            .attributes(easing_dict={"radius": easing.in_out})
            .keystate(s1, at=0.0)
            .transition(easing_dict={"radius": easing.step})
            .keystate(s2, at=1.0)
        )

        # Step easing: at t=0.25, step returns 0.0, so radius should be 0
        result = elem.get_frame(0.25)
        assert result.radius == pytest.approx(0, abs=0.1)

        # Step easing: at t=0.75, step returns 1.0, so radius should be 100
        result = elem.get_frame(0.75)
        assert result.radius == pytest.approx(100, abs=0.1)

    def test_element_easing_applies_to_all_segments(self):
        """Element-level attribute_easing should apply to segments without explicit easing."""
        s1 = CircleState(pos=Point2D(0, 0), radius=0)
        s2 = CircleState(pos=Point2D(0, 0), radius=100)
        s3 = CircleState(pos=Point2D(0, 0), radius=200)

        elem = (
            VElement()
            .attributes(easing_dict={"radius": easing.step})
            .keystate(s1, at=0.0)
            .keystate(s2, at=0.5)
            .keystate(s3, at=1.0)
        )

        # Both segments should use step easing
        assert elem.get_frame(0.1).radius == pytest.approx(0, abs=0.1)
        assert elem.get_frame(0.4).radius == pytest.approx(100, abs=0.1)
        assert elem.get_frame(0.6).radius == pytest.approx(100, abs=0.1)
        assert elem.get_frame(0.9).radius == pytest.approx(200, abs=0.1)


# ---------------------------------------------------------------------------
# 5. Attribute keystates (per-field timelines)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAttributeKeystates:
    """Verify per-field independent timelines."""

    def test_radius_timeline_overrides_main(self):
        """Attribute keystates should override main interpolation for that field."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        s2 = CircleState(pos=Point2D(100, 0), radius=50)

        elem = (
            VElement()
            .attributes(keystates_dict={"radius": [10, 90]})
            .keystate(s1, at=0.0)
            .keystate(s2, at=1.0)
        )

        result = elem.get_frame(0.5)
        # pos should interpolate normally
        assert result.pos.x == pytest.approx(50)
        # radius should come from attribute timeline: lerp(10, 90, 0.5) = 50
        assert result.radius == pytest.approx(50)

        # At t=0: radius from timeline = 10, not from main keystate (50)
        result_start = elem.get_frame(0.0)
        assert result_start.radius == pytest.approx(10)

    def test_attribute_keystates_with_explicit_times(self):
        """Attribute keystates with explicit timing."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        s2 = CircleState(pos=Point2D(100, 0), radius=50)

        elem = (
            VElement()
            .attributes(keystates_dict={
                "radius": [(0.0, 10), (0.5, 100), (1.0, 10)]
            })
            .keystate(s1, at=0.0)
            .keystate(s2, at=1.0)
        )

        assert elem.get_frame(0.0).radius == pytest.approx(10)
        assert elem.get_frame(0.5).radius == pytest.approx(100)
        assert elem.get_frame(1.0).radius == pytest.approx(10)

        # Midpoint between 0.0→0.5 should be lerp(10, 100, 0.5) = 55
        assert elem.get_frame(0.25).radius == pytest.approx(55)

    def test_attribute_keystates_extend_to_full_range(self):
        """Attribute timelines should extend first/last values to 0.0 and 1.0."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        s2 = CircleState(pos=Point2D(100, 0), radius=50)

        elem = (
            VElement()
            .attributes(keystates_dict={
                "radius": [(0.3, 20), (0.7, 80)]
            })
            .keystate(s1, at=0.0)
            .keystate(s2, at=1.0)
        )

        # Before timeline start: should hold first value
        assert elem.get_frame(0.0).radius == pytest.approx(20)
        assert elem.get_frame(0.2).radius == pytest.approx(20)

        # After timeline end: should hold last value
        assert elem.get_frame(0.8).radius == pytest.approx(80)
        assert elem.get_frame(1.0).radius == pytest.approx(80)


# ---------------------------------------------------------------------------
# 6. Dual-state keystates
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDualStateKeystates:
    """Verify instant state switching with dual-state keystates."""

    def test_instant_switch_at_boundary(self):
        """Dual-state keystate should switch instantly."""
        yellow = CircleState(pos=Point2D(0, 0), radius=50, fill_color=Color("#FFFF00"))
        green = CircleState(pos=Point2D(0, 0), radius=50, fill_color=Color("#00FF00"))
        red = CircleState(pos=Point2D(0, 0), radius=50, fill_color=Color("#FF0000"))

        elem = (
            VElement()
            .keystate(yellow, at=0.0)
            .keystate([yellow, green], at=0.5)
            .keystate(green, at=1.0)
        )

        # Before switch: interpolating toward yellow (incoming)
        before = elem.get_frame(0.25)
        assert before.fill_color.r == yellow.fill_color.r

        # At exactly 0.5: render_index=0 means incoming (yellow)
        at_switch = elem.get_frame(0.5)
        assert at_switch.fill_color.r == yellow.fill_color.r
        assert at_switch.fill_color.g == yellow.fill_color.g

        # After switch: interpolating from green (outgoing)
        after = elem.get_frame(0.75)
        assert after.fill_color.g > 0  # Should be between green and green

    def test_render_index_1(self):
        """render_index=1 should render the outgoing state at exact time."""
        red = CircleState(pos=Point2D(0, 0), radius=50, fill_color=Color("#FF0000"))
        blue = CircleState(pos=Point2D(0, 0), radius=50, fill_color=Color("#0000FF"))

        elem = (
            VElement()
            .keystate(red, at=0.0)
            .keystate([red, blue], at=0.5, render_index=1)
            .keystate(blue, at=1.0)
        )

        # At exactly 0.5 with render_index=1: should render outgoing (blue)
        at_switch = elem.get_frame(0.5)
        assert at_switch.fill_color.b == blue.fill_color.b
        assert at_switch.fill_color.r == blue.fill_color.r


# ---------------------------------------------------------------------------
# 7. Element existence (timeline boundaries)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestElementExistence:
    """Verify element only exists within its keystate timeline."""

    def test_element_none_outside_range(self):
        """get_frame should return None outside keystate range."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        s2 = CircleState(pos=Point2D(100, 0), radius=50)

        elem = (
            VElement()
            .keystate(s1, at=0.3)
            .keystate(s2, at=0.7)
        )

        assert elem.get_frame(0.0) is None
        assert elem.get_frame(0.1) is None
        assert elem.get_frame(0.3) is not None
        assert elem.get_frame(0.5) is not None
        assert elem.get_frame(0.7) is not None
        assert elem.get_frame(0.9) is None

    def test_single_keystate_exists_only_at_time(self):
        """Single keystate element should only exist at its exact time."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50)
        elem = VElement().keystate(s1, at=0.5)

        assert elem.get_frame(0.0) is None
        assert elem.get_frame(0.5) is not None
        assert elem.get_frame(1.0) is None


# ---------------------------------------------------------------------------
# 8. Skip-identical optimization
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSkipIdenticalOptimization:
    """Verify that identical fields are skipped during interpolation."""

    def test_identical_fields_not_recomputed(self, engine):
        """Fields with equal start/end should be skipped (returned as-is)."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50, opacity=0.8)
        s2 = CircleState(pos=Point2D(100, 0), radius=50, opacity=0.8)

        changed, field_values = InterpolationEngine.compute_changed_fields(
            s1, s2, attribute_keystates_fields=set()
        )

        assert "pos" in changed
        assert "radius" not in changed
        assert "opacity" not in changed

    def test_result_correct_when_only_some_fields_change(self, engine):
        """When only some fields change, unchanged fields should retain their values."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50, opacity=0.5)
        s2 = CircleState(pos=Point2D(100, 0), radius=50, opacity=0.5)

        result = engine.create_eased_state(
            s1, s2, t=0.5,
            segment_easing_overrides=None,
            attribute_keystates_fields=set(),
        )

        assert result.pos.x == pytest.approx(50)
        assert result.radius == 50
        assert result.opacity == 0.5


# ---------------------------------------------------------------------------
# 9. Binary search segment lookup
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSegmentLookup:
    """Verify binary search finds the correct segment for multi-keystate elements."""

    def test_many_keystates_correct_interpolation(self):
        """With many keystates, each segment should interpolate correctly."""
        states = [
            CircleState(pos=Point2D(i * 10, 0), radius=50) for i in range(11)
        ]
        elem = VElement().keystates(states)

        # t=0.05 → in segment 0→1: pos should be near 5
        r = elem.get_frame(0.05)
        assert r.pos.x == pytest.approx(5, abs=0.5)

        # t=0.95 → in segment 9→10: pos should be near 95
        r = elem.get_frame(0.95)
        assert r.pos.x == pytest.approx(95, abs=0.5)

        # t=0.5 → at keystate 5: pos should be 50
        r = elem.get_frame(0.5)
        assert r.pos.x == pytest.approx(50, abs=0.5)

    def test_exact_keystate_boundary_returns_keystate_state(self):
        """At exact keystate time, should return that keystate's state directly."""
        s1 = CircleState(pos=Point2D(0, 0), radius=10)
        s2 = CircleState(pos=Point2D(50, 0), radius=20)
        s3 = CircleState(pos=Point2D(100, 0), radius=30)

        elem = (
            VElement()
            .keystate(s1, at=0.0)
            .keystate(s2, at=0.5)
            .keystate(s3, at=1.0)
        )

        r = elem.get_frame(0.5)
        assert r.pos.x == pytest.approx(50)
        assert r.radius == pytest.approx(20)


# ---------------------------------------------------------------------------
# 10. Inbetween flag and VertexRenderer selection
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestInbetweenFlag:
    """Verify the inbetween flag is set during cross-type vertex morphing."""

    def test_inbetween_flag_for_different_vertex_types(self):
        """Morphing between different VertexState types should set inbetween=True."""
        star = StarState(pos=Point2D(0, 0), outer_radius=50, inner_radius=20)
        circle = CircleState(pos=Point2D(0, 0), radius=50)

        elem = VElement().keystate(star, at=0.0).keystate(circle, at=1.0)

        # Access the interpolator directly to check the flag
        elem._ensure_built()
        _, inbetween = elem._interpolator.get_state_at_time(0.5)
        assert inbetween is True

    def test_no_inbetween_for_same_type(self):
        """Same VertexState types should not set inbetween."""
        c1 = CircleState(pos=Point2D(0, 0), radius=50)
        c2 = CircleState(pos=Point2D(100, 0), radius=100)

        elem = VElement().keystate(c1, at=0.0).keystate(c2, at=1.0)

        elem._ensure_built()
        _, inbetween = elem._interpolator.get_state_at_time(0.5)
        assert inbetween is False


# ---------------------------------------------------------------------------
# 11. TransitionConfig.linear_angle_interpolation merge bug (Fix 1)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBuilderMergeBugFix:
    """Verify that linear_angle_interpolation is preserved during merge."""

    def test_linear_angle_survives_element_interpolation_merge(self):
        """Bug fix: _merge_element_path_into_transition must preserve linear_angle_interpolation."""
        s1 = CircleState(pos=Point2D(0, 0), radius=50, rotation=0)
        s2 = CircleState(pos=Point2D(100, 0), radius=50, rotation=720)

        def my_curve(p1, p2, t):
            return Point2D(t * 100, 0)

        elem = (
            VElement()
            .attributes(interpolation_dict={"pos": my_curve})
            .keystate(s1, at=0.0)
            .transition(linear_angle_interpolation=True)
            .keystate(s2, at=1.0)
        )

        elem._ensure_built()
        # After merge, the keystate's transition should still have the flag
        tc = elem._keystates_list[0].transition_config
        assert tc is not None
        assert tc.linear_angle_interpolation is True
        # And the actual interpolation should work
        result = elem.get_frame(0.5)
        assert result.rotation == pytest.approx(360)


# ---------------------------------------------------------------------------
# 12. Default transition
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDefaultTransition:
    """Verify default_transition applies to all segments."""

    def test_default_transition_applies_to_all(self):
        """default_transition easing should apply to every segment."""
        s1 = CircleState(pos=Point2D(0, 0), radius=0)
        s2 = CircleState(pos=Point2D(0, 0), radius=100)
        s3 = CircleState(pos=Point2D(0, 0), radius=200)

        elem = (
            VElement()
            .default_transition(easing_dict={"radius": easing.step})
            .keystate(s1, at=0.0)
            .keystate(s2, at=0.5)
            .keystate(s3, at=1.0)
        )

        # Step easing in both segments
        assert elem.get_frame(0.1).radius == pytest.approx(0, abs=0.1)
        assert elem.get_frame(0.4).radius == pytest.approx(100, abs=0.1)
        assert elem.get_frame(0.6).radius == pytest.approx(100, abs=0.1)
        assert elem.get_frame(0.9).radius == pytest.approx(200, abs=0.1)

    def test_segment_transition_overrides_default(self):
        """Explicit segment transition should override default_transition."""
        s1 = CircleState(pos=Point2D(0, 0), radius=0)
        s2 = CircleState(pos=Point2D(0, 0), radius=100)
        s3 = CircleState(pos=Point2D(0, 0), radius=200)

        elem = (
            VElement()
            .default_transition(easing_dict={"radius": easing.step})
            .keystate(s1, at=0.0)
            .transition(easing_dict={"radius": easing.linear})  # Override for seg 0
            .keystate(s2, at=0.5)
            .keystate(s3, at=1.0)  # Seg 1 uses default (step)
        )

        # Segment 0: linear → at t=0.25, radius = lerp(0, 100, 0.5) = 50
        assert elem.get_frame(0.25).radius == pytest.approx(50, abs=1)

        # Segment 1: step → at t=0.6 (segment_t=0.2), radius should still be 100
        assert elem.get_frame(0.6).radius == pytest.approx(100, abs=0.1)
