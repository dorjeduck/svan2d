"""Where CircleTextState puts its text on the circle, in both backends.

A single "X" is drawn and its position read back as the angle of its pixels'
centroid, in Cartesian degrees (0 = East, counter-clockwise), the convention
`angles` is given in. `rotation` turns the element as it turns every other
state: counter-clockwise, by its transform.
"""

from __future__ import annotations

import math

import pytest

np = pytest.importorskip("numpy")
skia = pytest.importorskip("skia")
pytest.importorskip("resvg_py")

from svan2d.converter.resvg_svg_converter import ResvgSvgConverter
from svan2d.converter.skia_svg_converter import SkiaSvgConverter
from svan2d.core import Color
from svan2d.primitive.state.circle_text import CircleTextState
from svan2d.velement import VElement
from svan2d.vscene import VScene

S = 400


def _angle(converter, tmp_path, **fields) -> float:
    state = CircleTextState(fill_color=Color("#ffffff"), font_size=30, radius=120, **fields)
    scene = VScene(width=S, height=S).add_element(VElement(state=state))
    out = str(tmp_path / "text.png")
    res = converter()._convert_to_png(scene, out, 0.0, S, S)
    assert res["success"], res
    alpha = skia.Image.open(out).toarray()[:, :, 3]
    ys, xs = np.nonzero(alpha > 128)
    assert len(xs) > 0, "nothing drawn"
    return math.degrees(math.atan2(S / 2 - ys.mean(), xs.mean() - S / 2)) % 360


def _assert_at(got: float, want: float) -> None:
    assert abs((got - want + 180) % 360 - 180) < 3, f"at {got:.1f}°, want {want}°"


CONVERTERS = [SkiaSvgConverter, ResvgSvgConverter]


@pytest.mark.integration
@pytest.mark.parametrize("converter", CONVERTERS)
@pytest.mark.parametrize("inward", [True, False])
@pytest.mark.parametrize("angle", [0, 45, 180])
def test_angles_place_text_at_that_angle(tmp_path, converter, inward, angle):
    got = _angle(converter, tmp_path, text=["X"], angles=[angle], text_facing_inward=inward)
    _assert_at(got, angle)


@pytest.mark.integration
@pytest.mark.parametrize("converter", CONVERTERS)
@pytest.mark.parametrize("inward", [True, False])
@pytest.mark.parametrize("text", ["X", ["X"]], ids=["single", "list"])
def test_rotation_turns_text_once(tmp_path, converter, inward, text):
    # Unrotated, a single text and a list's first entry both sit at the top.
    got = _angle(converter, tmp_path, text=text, rotation=30, text_facing_inward=inward)
    _assert_at(got, 120)


@pytest.mark.integration
@pytest.mark.parametrize("converter", CONVERTERS)
@pytest.mark.parametrize("inward", [True, False])
def test_rotation_turns_angles_once(tmp_path, converter, inward):
    got = _angle(converter, tmp_path, text=["X"], angles=[0], rotation=30,
                 text_facing_inward=inward)
    _assert_at(got, 30)
