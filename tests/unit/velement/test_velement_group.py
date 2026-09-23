"""Tests for VElementGroup."""

from svan2d.velement.velement_group import VElementGroup, VElementGroupState


class TestFrameFn:
    """Tests for frame_fn path of VElementGroup (Finding #14)."""

    def test_frame_fn_group_is_animatable(self):
        """A VElementGroup constructed via frame_fn should report is_animatable() as True
        without raising AttributeError on _keystates_list."""
        group = VElementGroup().frame_fn(lambda base, t: VElementGroupState())
        assert group.is_animatable() is True

    def test_frame_fn_group_get_frame(self):
        """get_frame on a frame_fn-backed VElementGroup returns the fn's output."""
        expected = VElementGroupState(rotation=45.0)
        group = VElementGroup().frame_fn(lambda base, t: expected)
        assert group.get_frame(0.5) is expected

    def test_frame_fn_group_render(self):
        """render_at_frame_time on a frame_fn-backed VElementGroup produces a Group."""
        group = VElementGroup().frame_fn(lambda base, t: VElementGroupState())
        result = group.render_at_frame_time(0.5)
        assert result is not None


class TestGroupClipping:
    """A group-level .clip() must reach the SVG, not just the group's state."""

    @staticmethod
    def _render_svg(root) -> str:
        import drawsvg as dw

        drawing = dw.Drawing(400, 400, origin="center")
        drawing.append(root.render_at_frame_time(0.0, drawing))
        return drawing.as_svg()

    def test_clip_element_emits_a_clip_path(self):
        """The clip element must produce a <clipPath> def and a clip-path reference.

        Before the fix _render_group_state resolved the clip into
        state.clip_states and then built dw.Group() with only transform and
        opacity, so the resolved value was never read and the clip vanished.
        """
        from svan2d.core.color import Color
        from svan2d.primitive.state.circle import CircleState
        from svan2d.primitive.state.rectangle import RectangleState
        from svan2d.velement.velement import VElement

        clipper = VElement(state=CircleState(radius=40, fill_color=Color("#000000")))
        child = VElement(
            state=RectangleState(width=200, height=200, fill_color=Color("#FF0000"))
        )
        group = (
            VElementGroup(elements=[child])
            .keystate(VElementGroupState())
            .clip(clipper)
        )

        svg = self._render_svg(group)
        assert "<clipPath" in svg
        assert "clip-path=" in svg

    def test_no_clip_leaves_the_output_unchanged(self):
        """Without a clip the group must render exactly as before: no extra nesting."""
        from svan2d.core.color import Color
        from svan2d.primitive.state.rectangle import RectangleState
        from svan2d.velement.velement import VElement

        child = VElement(
            state=RectangleState(width=200, height=200, fill_color=Color("#FF0000"))
        )
        group = VElementGroup(elements=[child]).keystate(VElementGroupState())

        svg = self._render_svg(group)
        assert "<clipPath" not in svg
        assert "clip-path=" not in svg
        assert svg.count("<g") == 1


class TestGroupEasing:
    def test_group_easing_alone_eases_the_children(self):
        from svan2d.core.point2d import Point2D
        from svan2d.primitive.state.circle import CircleState
        from svan2d.transition import easing
        from svan2d.velement import VElement

        child = (
            VElement()
            .keystate(CircleState(radius=5, pos=Point2D(0, 0)), at=0.0)
            .keystate(CircleState(radius=5, pos=Point2D(100, 0)), at=1.0)
        )
        group = VElementGroup(elements=[child], group_easing=easing.in_cubic)
        group.get_frame(0.5)
        assert group._last_frame_time == easing.in_cubic(0.5)
        from svan2d.vscene import VScene

        svg = VScene(width=200, height=100).add_element(group).to_svg(frame_time=0.5, log=False)
        assert f"translate({100 * easing.in_cubic(0.5)}," in svg
