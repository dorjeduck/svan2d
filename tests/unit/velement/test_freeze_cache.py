"""Tests for the auto-freeze cache (is_final State marker + _frozen_render).

Real-world usage pattern: animate to a final state by some t<1.0, then add a
hold keystate at t=1.0 with the same state, so the element persists for the
rest of the scene. The interpolator detects the constant tail segment and
stamps `is_final=True`; VScene caches the rendered element.
"""

from dataclasses import replace

from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.primitive.effect.filter.gaussian_blur import GaussianBlurFilter
from svan2d.primitive.renderer.circle import CircleRenderer
from svan2d.primitive.state.circle import CircleState
from svan2d.velement import VElement, VElementGroup
from svan2d.velement.velement_group import VElementGroupState
from svan2d.vscene.vscene import VScene


def _circle(at_pos: Point2D, color: Color = Color("red"), z: float = 0.0) -> CircleState:
    return CircleState(pos=at_pos, radius=10, fill_color=color, z_index=z)


def _animated_then_held(start_pos, end_pos, anim_end=0.4):
    """Element that animates from start to end by anim_end, then holds at t=1.0."""
    final = _circle(end_pos)
    return (
        VElement()
        .renderer(CircleRenderer())
        .keystate(_circle(start_pos), at=0.0)
        .keystate(final, at=anim_end)
        .keystate(final, at=1.0)
    )


class TestIsFinalAutoStamp:
    def test_state_is_final_in_constant_tail_segment(self):
        elem = _animated_then_held(Point2D(0, 0), Point2D(50, 0), anim_end=0.4)

        mid = elem.get_frame(0.2)
        assert mid is not None
        assert mid.is_final is False

        # In the constant tail segment (0.4 → 1.0)
        end = elem.get_frame(0.7)
        assert end is not None
        assert end.is_final is True

    def test_is_final_false_when_attribute_timeline_still_running(self):
        final = _circle(Point2D(50, 0))
        elem = (
            VElement()
            .renderer(CircleRenderer())
            .keystate(_circle(Point2D(0, 0)), at=0.0)
            .keystate(final, at=0.3)
            .keystate(final, at=1.0)
            .attributes(
                keystates_dict={
                    "fill_color": [
                        (0.0, Color("red")),
                        (0.6, Color("blue")),
                    ]
                }
            )
        )
        # Inside the constant tail but the color timeline is still animating
        mid = elem.get_frame(0.4)
        assert mid is not None
        assert mid.is_final is False

        # Past the color timeline's last event
        end = elem.get_frame(0.7)
        assert end is not None
        assert end.is_final is True

    def test_state_equality_ignores_is_final(self):
        a = _circle(Point2D(0, 0))
        b = replace(a, is_final=True)
        assert a == b


class TestFrozenRenderInScene:
    def test_frozen_render_set_after_constant_tail_frame(self):
        elem = _animated_then_held(Point2D(0, 0), Point2D(50, 0), anim_end=0.4)
        scene = VScene(width=100, height=100).add_element(elem)

        scene.to_drawing(frame_time=0.5)
        assert elem._frozen_render is not None
        assert elem._frozen_state is not None
        assert elem._frozen_state.is_final is True

        first_frozen = elem._frozen_render
        scene.to_drawing(frame_time=0.9)
        assert elem._frozen_render is first_frozen

    def test_frozen_render_not_set_during_animation(self):
        elem = _animated_then_held(Point2D(0, 0), Point2D(50, 0), anim_end=0.8)
        scene = VScene(width=100, height=100).add_element(elem)
        scene.to_drawing(frame_time=0.4)
        assert elem._frozen_render is None


class TestCacheUnsafeStaysLive:
    def test_filter_blocks_freeze(self):
        final = replace(
            _circle(Point2D(50, 0)), filter=GaussianBlurFilter(std_deviation=2)
        )
        elem = (
            VElement()
            .renderer(CircleRenderer())
            .keystate(_circle(Point2D(0, 0)), at=0.0)
            .keystate(final, at=0.4)
            .keystate(final, at=1.0)
        )
        scene = VScene(width=100, height=100).add_element(elem)
        scene.to_drawing(frame_time=0.6)
        assert elem._frozen_render is None


class TestFrameFnManualFlag:
    def test_user_set_is_final_via_frame_fn(self):
        base = _circle(Point2D(0, 0))

        def fn(state, t):
            new_state = replace(base, pos=Point2D(20 * t, 0))
            if t >= 0.5:
                new_state = replace(new_state, is_final=True)
            return new_state

        elem = VElement().renderer(CircleRenderer()).frame_fn(fn, base_state=base)
        scene = VScene(width=100, height=100).add_element(elem)

        scene.to_drawing(frame_time=0.3)
        assert elem._frozen_render is None

        scene.to_drawing(frame_time=0.6)
        assert elem._frozen_render is not None
        first_frozen = elem._frozen_render

        scene.to_drawing(frame_time=0.9)
        assert elem._frozen_render is first_frozen


class TestVElementGroupAndRule:
    def test_group_freezes_only_when_all_children_final(self):
        early = _animated_then_held(Point2D(0, 0), Point2D(10, 0), anim_end=0.2)
        late = _animated_then_held(Point2D(0, 30), Point2D(10, 30), anim_end=0.7)
        gs = VElementGroupState(pos=Point2D(0, 0))
        group = (
            VElementGroup(elements=[early, late])
            .keystate(gs, at=0.0)
            .keystate(gs, at=0.3)
            .keystate(gs, at=1.0)
        )
        scene = VScene(width=200, height=200).add_element(group)

        # Past early child but before late child — group must NOT freeze
        scene.to_drawing(frame_time=0.4)
        assert group._frozen_render is None

        # Past every child — group freezes
        scene.to_drawing(frame_time=0.8)
        assert group._frozen_render is not None
