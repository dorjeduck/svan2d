"""Tests for VElement.element_easing."""

from svan2d.core.point2d import Point2D
from svan2d.primitive.state.circle import CircleState
from svan2d.transition import easing
from svan2d.velement import VElement
from svan2d.vscene import VScene


def _x_at(element, t):
    state = element.get_frame(t)
    assert state is not None
    return state.pos.x


def _moving():
    return (
        VElement()
        .keystate(CircleState(radius=5, pos=Point2D(0, 0)), at=0.0)
        .keystate(CircleState(radius=5, pos=Point2D(100, 0)), at=1.0)
    )


class TestElementEasing:
    def test_keystates_see_the_eased_time(self):
        element = _moving().element_easing(easing.in_cubic)
        assert _x_at(element, 0.5) == 100 * easing.in_cubic(0.5)

    def test_frame_fn_sees_the_eased_time(self):
        seen = []

        def frame(state, t):
            seen.append(t)
            return state

        element = (
            VElement()
            .frame_fn(frame, base_state=CircleState(radius=5))
            .element_easing(lambda t: t / 2)
        )
        element.get_frame(0.5)
        assert seen == [0.25]

    def test_kept_through_later_chaining(self):
        element = (
            VElement()
            .element_easing(easing.in_cubic)
            .keystate(CircleState(radius=5, pos=Point2D(0, 0)), at=0.0)
            .keystate(CircleState(radius=5, pos=Point2D(100, 0)), at=1.0)
        )
        assert _x_at(element, 0.5) == 100 * easing.in_cubic(0.5)

    def test_none_removes_it(self):
        element = _moving().element_easing(easing.in_cubic).element_easing(None)
        assert _x_at(element, 0.5) == 50

    def test_render_uses_the_eased_time(self):
        element = _moving().element_easing(easing.in_cubic)
        svg = VScene(width=200, height=100).add_element(element).to_svg(
            frame_time=0.5, log=False
        )
        assert f"translate({100 * easing.in_cubic(0.5)}," in svg
