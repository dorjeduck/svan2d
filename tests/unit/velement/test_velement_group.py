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
