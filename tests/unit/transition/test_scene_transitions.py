"""Scene transitions keep the defs of the scenes they blend."""

import re

import pytest

from svan2d.core import Color
from svan2d.primitive.state.circle import CircleState
from svan2d.primitive.state.rectangle import RectangleState
from svan2d.transition.scene import Fade, Iris, Slide, Wipe, Zoom
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.vscene.vscene_sequence import VSceneSequence


def _clipped_scene(color: str) -> VScene:
    return VScene(width=100, height=100, background=Color("#000")).add_element(
        VElement(state=RectangleState(
            width=80, height=80, fill_color=Color(color), clip_state=CircleState(radius=30)
        ))
    )


@pytest.mark.unit
@pytest.mark.parametrize("transition", [
    Fade(duration=0.2),
    Iris(direction="open", duration=0.2),
    Iris(direction="close", duration=0.2),
    Slide(duration=0.2),
    Wipe(duration=0.2),
    Zoom(duration=0.2),
])
def test_every_reference_mid_transition_has_its_def(transition):
    sequence = (
        VSceneSequence()
        .scene(_clipped_scene("#f00"), 0.4)
        .transition(transition)
        .scene(_clipped_scene("#00f"), 0.4)
    )
    svg = sequence.to_svg(frame_time=0.5, log=False)
    referenced = set(re.findall(r'url\(#([\w-]+)\)', svg))
    defined = set(re.findall(r' id="([\w-]+)"', svg))
    assert len(referenced) >= 2
    assert referenced <= defined
