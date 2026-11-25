"""Letter spacing in em: a share of the font size, as SVG and CSS write it."""

from dataclasses import replace

import pytest

from svan2d.core import Em
from svan2d.primitive import TextState
from svan2d.transition.easing import linear
from svan2d.velement import VElement
from svan2d.vscene import VScene


@pytest.mark.unit
class TestEm:
    def test_parse_reads_the_number_before_em(self):
        assert Em.parse("0.04em") == Em(0.04)
        assert Em.parse(" -0.5em ") == Em(-0.5)

    @pytest.mark.parametrize("text", ["0.04px", "0.04", "em", "wide em"])
    def test_parse_refuses_anything_else(self, text):
        with pytest.raises(ValueError):
            Em.parse(text)

    def test_px_is_the_share_of_the_font_size(self):
        assert Em(0.25).px(40) == pytest.approx(10)


@pytest.mark.unit
class TestTextStateLetterSpacing:
    def test_a_number_is_pixels(self):
        assert TextState(font_size=50, letter_spacing=5).letter_spacing_px == 5

    def test_an_em_string_becomes_em(self):
        state = TextState(font_size=50, letter_spacing="0.04em")
        assert state.letter_spacing == Em(0.04)
        assert state.letter_spacing_px == pytest.approx(2)

    def test_a_bad_string_fails_when_the_text_is_made(self):
        with pytest.raises(ValueError):
            TextState(letter_spacing="0.04px")

    def test_em_follows_a_new_font_size(self):
        state = TextState(font_size=50, letter_spacing=Em(0.04))
        assert replace(state, font_size=100).letter_spacing_px == pytest.approx(4)


def _halfway(start: TextState, end: TextState) -> TextState:
    element = (
        VElement()
        .keystate(start, at=0.0)
        .transition(easing=linear)
        .keystate(end, at=1.0)
    )
    return element.get_frame(0.5)


@pytest.mark.unit
class TestLetterSpacingAnimation:
    def test_em_to_em_blends_in_em(self):
        middle = _halfway(
            TextState(font_size=20, letter_spacing=Em(0.02)),
            TextState(font_size=60, letter_spacing=Em(0.1)),
        )
        assert isinstance(middle.letter_spacing, Em)
        assert middle.letter_spacing.value == pytest.approx(0.06)
        assert middle.letter_spacing_px == pytest.approx(0.06 * 40)

    def test_pixels_to_em_blends_in_pixels(self):
        middle = _halfway(
            TextState(font_size=20, letter_spacing=2),
            TextState(font_size=60, letter_spacing=Em(0.1)),
        )
        assert middle.letter_spacing == pytest.approx((2 + 6) / 2)

    def test_pixels_to_pixels_blend_as_before(self):
        middle = _halfway(
            TextState(letter_spacing=2),
            TextState(letter_spacing=10),
        )
        assert middle.letter_spacing == pytest.approx(6)

    def test_an_attribute_timeline_blends_em(self):
        state = TextState(font_size=50)
        element = (
            VElement()
            .keystates([state, state])
            .attributes(
                easing_dict={"letter_spacing": linear},
                keystates_dict={"letter_spacing": [(0.0, Em(0.0)), (1.0, Em(0.2))]},
            )
        )
        middle = element.get_frame(0.5)
        assert isinstance(middle.letter_spacing, Em)
        assert middle.letter_spacing.value == pytest.approx(0.1)


@pytest.mark.unit
def test_svg_writes_em_spacing_as_pixels():
    state = TextState(text="Hi", font_size=40, letter_spacing="0.25em")
    svg = (
        VScene(width=200, height=100)
        .add_element(VElement(state=state))
        .to_svg(log=False)
    )
    assert 'letter-spacing="10.0"' in svg
