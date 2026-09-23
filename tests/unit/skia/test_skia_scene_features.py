"""The Skia backend against resvg for scene-level features.

Covers clipping and masking at element, group and scene level. Every case
renders the same scene through Skia and through resvg and requires the two to
agree on all four channels, apart from a thin antialiased edge band.
"""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")
skia = pytest.importorskip("skia")
pytest.importorskip("resvg_py")

from svan2d.converter.resvg_svg_converter import ResvgSvgConverter
from svan2d.converter.skia_svg_converter import SkiaSvgConverter
from svan2d.core import Color
from svan2d.core.point2d import Point2D
from svan2d.primitive.state.circle import CircleState
from svan2d.primitive.state.rectangle import RectangleState
from svan2d.primitive.state.triangle import TriangleState
from svan2d.skia import check_scene
from svan2d.velement import VElement, VElementGroup
from svan2d.velement.velement_group import VElementGroupState
from svan2d.vscene import VScene

W = H = 200


def _png(converter, scene, tmp_path, name, t, w, h):
    out = str(tmp_path / name)
    res = converter._convert_to_png(scene, out, t, w, h)
    assert res["success"], res
    return skia.Image.open(out).toarray().astype(int)  # H x W x 4


def assert_matches_resvg(scene, tmp_path, t=0.0, w=W, h=H):
    assert check_scene(scene) == []
    got = _png(SkiaSvgConverter(), scene, tmp_path, "skia.png", t, w, h)
    want = _png(ResvgSvgConverter(), scene, tmp_path, "resvg.png", t, w, h)
    diff = np.abs(got - want).max(axis=2)
    differing = (diff > 40).mean()
    assert differing < 0.01, f"{differing:.3%} of pixels differ from resvg"
    # The scene must actually show something, or the match proves nothing.
    assert (want[:, :, 3] > 0).any()


def _scene(**kwargs) -> VScene:
    return VScene(width=W, height=H, background=Color("#102030"), **kwargs)


def _rect(**kwargs) -> RectangleState:
    return RectangleState(width=160, height=120, fill_color=Color("#ff8000"), **kwargs)


# --------------------------------------------------------------------------
# Element level
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_element_clip_state(tmp_path):
    clip = CircleState(radius=50, pos=Point2D(30, 20))
    element = VElement(state=_rect(pos=Point2D(-10, 15), rotation=20, clip_state=clip))
    assert_matches_resvg(_scene().add_element(element), tmp_path)


@pytest.mark.integration
def test_element_clip_states_are_a_union(tmp_path):
    clips = [
        CircleState(radius=35, pos=Point2D(-40, 0)),
        TriangleState(size=70, pos=Point2D(40, 10), rotation=30),
    ]
    element = VElement(state=_rect(clip_states=clips))
    assert_matches_resvg(_scene().add_element(element), tmp_path)


@pytest.mark.integration
def test_element_clip_ignores_clip_shape_paint(tmp_path):
    # A clip shape with no fill, a stroke and low opacity still clips by its
    # geometry alone.
    clip = CircleState(
        radius=50,
        fill_color=Color.NONE,
        stroke_color=Color("#fff"),
        stroke_width=20,
        opacity=0.3,
    )
    element = VElement(state=_rect(clip_state=clip))
    assert_matches_resvg(_scene().add_element(element), tmp_path)


@pytest.mark.integration
def test_element_clip_under_opacity(tmp_path):
    element = VElement(
        state=_rect(opacity=0.5, clip_state=CircleState(radius=55))
    )
    assert_matches_resvg(_scene().add_element(element), tmp_path)


@pytest.mark.integration
def test_velement_clip_attachment(tmp_path):
    element = VElement(state=_rect(pos=Point2D(10, -5))).clip(
        VElement(state=CircleState(radius=45, pos=Point2D(-20, 10)))
    )
    assert_matches_resvg(_scene().add_element(element), tmp_path)


@pytest.mark.integration
def test_element_mask_luminance(tmp_path):
    # A grey mask lets the content through by the mask's brightness.
    mask = CircleState(radius=60, fill_color=Color("#808080"), pos=Point2D(20, 0))
    element = VElement(state=_rect(mask_state=mask))
    assert_matches_resvg(_scene().add_element(element), tmp_path)


@pytest.mark.integration
def test_element_mask_opacity_and_default_fill(tmp_path):
    # No fill: the element path gives the mask a white one.
    mask = CircleState(radius=60, fill_color=Color.NONE, opacity=0.4)
    element = VElement(state=_rect(mask_state=mask))
    assert_matches_resvg(_scene().add_element(element), tmp_path)


@pytest.mark.integration
def test_element_mask_states_multiply(tmp_path):
    masks = [
        CircleState(radius=70, fill_color=Color("#c0c0c0"), pos=Point2D(-25, 0)),
        CircleState(radius=70, fill_color=Color("#a0a0a0"), pos=Point2D(25, 0)),
    ]
    element = VElement(state=_rect(mask_states=masks))
    assert_matches_resvg(_scene().add_element(element), tmp_path)


@pytest.mark.integration
def test_element_clip_and_mask_together(tmp_path):
    element = VElement(
        state=_rect(
            clip_state=CircleState(radius=55),
            mask_state=RectangleState(
                width=200, height=60, fill_color=Color("#b0b0b0"), pos=Point2D(0, 20)
            ),
        )
    )
    assert_matches_resvg(_scene().add_element(element), tmp_path)


# --------------------------------------------------------------------------
# Group level
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_group_clip_attachment(tmp_path):
    group = VElementGroup(
        elements=[
            VElement(state=CircleState(radius=40, pos=Point2D(-30, 0), fill_color=Color("#0f0"))),
            VElement(state=CircleState(radius=40, pos=Point2D(30, 0), fill_color=Color("#00f"))),
        ]
    ).keystate(VElementGroupState(pos=Point2D(10, 10), rotation=15))
    group = group.clip(VElement(state=RectangleState(width=100, height=50)))
    assert_matches_resvg(_scene().add_element(group), tmp_path)


# --------------------------------------------------------------------------
# Scene level
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_scene_clip_state(tmp_path):
    scene = _scene(
        clip_state=CircleState(radius=60, pos=Point2D(20, 30), fill_color=Color("#000"))
    ).add_element(VElement(state=_rect()))
    assert_matches_resvg(scene, tmp_path)


@pytest.mark.integration
def test_scene_mask_state(tmp_path):
    scene = _scene(
        mask_state=CircleState(radius=70, fill_color=Color("#909090"), pos=Point2D(-10, 20))
    ).add_element(VElement(state=_rect()))
    assert_matches_resvg(scene, tmp_path)


# --------------------------------------------------------------------------
# Camera and output scale
# --------------------------------------------------------------------------

from svan2d.core.enums import Origin
from svan2d.vscene.camera_state import CameraState
from svan2d.vscene.vscene_composite import VSceneComposite


def _content(origin=Origin.CENTER):
    # Three shapes, placed so a top-left scene shows them too.
    shift = Point2D(0, 0) if origin == Origin.CENTER else Point2D(W / 2, -H / 2)
    return [
        VElement(state=RectangleState(
            width=60, height=40, pos=Point2D(x + shift.x, y + shift.y), fill_color=Color(c)
        ))
        for x, y, c in ((-50, 30, "#ff8000"), (40, -20, "#00aaff"), (10, 50, "#88ff00"))
    ]


@pytest.mark.integration
@pytest.mark.parametrize("camera", [
    CameraState(scale=1.4),
    CameraState(pos=Point2D(15, -10)),
    CameraState(rotation=25),
    CameraState(scale=1.4, pos=Point2D(15, -10), rotation=20, pivot=Point2D(40, 30)),
])
def test_static_camera(tmp_path, camera):
    scene = _scene().add_elements(_content()).camera_keystate(camera, at=0.0)
    assert_matches_resvg(scene, tmp_path)


@pytest.mark.integration
@pytest.mark.parametrize("t", [0.0, 0.4, 1.0])
def test_camera_keystates(tmp_path, t):
    scene = (
        _scene()
        .add_elements(_content())
        .camera_keystate(CameraState(scale=1.0), at=0.0)
        .camera_keystate(CameraState(scale=2.0, pos=Point2D(30, 20), rotation=30), at=1.0)
    )
    assert_matches_resvg(scene, tmp_path, t=t)


@pytest.mark.integration
@pytest.mark.parametrize("origin", [Origin.CENTER, Origin.TOP_LEFT])
@pytest.mark.parametrize("t", [0.0, 0.5, 1.0])
def test_animated_camera(tmp_path, origin, t):
    center = Point2D(0, 0) if origin == Origin.CENTER else Point2D(W / 2, -H / 2)
    scene = (
        _scene(origin=origin)
        .add_elements(_content(origin))
        .animate_camera(
            scale=lambda t: 1 + t,
            offset=lambda t: Point2D(center.x + 30 * t, center.y + 10 * t),
        )
    )
    assert_matches_resvg(scene, tmp_path, t=t)


@pytest.mark.integration
@pytest.mark.parametrize("size", [(400, 400), (300, 200), (200, 320)])
def test_output_scale_with_camera_and_clip(tmp_path, size):
    scene = (
        _scene(clip_state=CircleState(radius=80, pos=Point2D(10, 5)))
        .add_elements(_content())
        .camera_keystate(
            CameraState(scale=1.3, rotation=15, pivot=Point2D(20, 10)), at=0.0
        )
    )
    assert_matches_resvg(scene, tmp_path, w=size[0], h=size[1])


# --------------------------------------------------------------------------
# Composites
# --------------------------------------------------------------------------


def _small(color, width=100, height=100, origin=Origin.CENTER, **kwargs):
    circle_pos = Point2D(0, 0) if origin == Origin.CENTER else Point2D(width / 2, -height / 2)
    return VScene(
        width=width, height=height, background=Color(color), origin=origin, **kwargs
    ).add_element(VElement(state=CircleState(
        radius=min(width, height) / 3, pos=circle_pos, fill_color=Color("#ffffff")
    )))


@pytest.mark.integration
@pytest.mark.parametrize("direction", ["horizontal", "vertical", "overlay"])
@pytest.mark.parametrize("origin", [Origin.CENTER, Origin.TOP_LEFT])
def test_composite_layout(tmp_path, direction, origin):
    composite = VSceneComposite(
        [_small("#aa2222", origin=origin), _small("#22aa22", 150, 80, origin=origin)],
        direction=direction,
        gap=10,
        background=Color("#000040"),
    )
    w, h = int(composite.width), int(composite.height)
    assert_matches_resvg(composite, tmp_path, w=w, h=h)
    assert_matches_resvg(composite, tmp_path, w=w * 2, h=h * 2)


@pytest.mark.integration
def test_nested_composite(tmp_path):
    row = VSceneComposite([_small("#aa2222"), _small("#22aa22")], direction="horizontal")
    grid = VSceneComposite([row, _small("#2222aa", 200, 60)], direction="vertical", gap=6)
    assert_matches_resvg(grid, tmp_path, w=int(grid.width), h=int(grid.height))


@pytest.mark.integration
@pytest.mark.parametrize("t", [0.0, 0.5, 1.0])
def test_composite_of_clipped_scene_with_moving_camera(tmp_path, t):
    # Moonscape's shape: a margin, a square stage clipped to itself with a
    # camera closing in, and a band below, laid over a full-size ground.
    stage = (
        VScene(width=160, height=160, background=None,
               clip_state=RectangleState(width=160, height=160))
        .add_elements(_content())
        .animate_camera(scale=lambda t: 1 + 3 * t, offset=lambda t: Point2D(40 * t, -20 * t))
    )
    stacked = VSceneComposite(
        [VScene(width=160, height=20, background=None), stage, _small("#303030", 160, 60)],
        direction="vertical",
    )
    ground = VScene(width=stacked.width, height=stacked.height,
                    background=Color("#05060d"), origin=Origin.TOP_LEFT)
    composite = VSceneComposite([ground, stacked], direction="overlay")
    w, h = int(composite.width), int(composite.height)
    assert_matches_resvg(composite, tmp_path, t=t, w=w, h=h)
    assert_matches_resvg(composite, tmp_path, t=t, w=w * 3, h=h * 3)


# --------------------------------------------------------------------------
# Sequences and transitions
# --------------------------------------------------------------------------

from svan2d.transition import easing
from svan2d.transition.scene import Fade, Iris, Slide, Wipe, Zoom
from svan2d.vscene.vscene_sequence import VSceneSequence


def _moving(color, origin=Origin.CENTER):
    shift = Point2D(0, 0) if origin == Origin.CENTER else Point2D(W / 2, -H / 2)
    return VScene(width=W, height=H, background=Color(color), origin=origin).add_element(
        VElement()
        .keystate(CircleState(radius=20, pos=Point2D(shift.x - 50, shift.y),
                              fill_color=Color("#ffffff")), at=0.0)
        .keystate(CircleState(radius=40, pos=Point2D(shift.x + 50, shift.y + 20),
                              fill_color=Color("#ffcc00")), at=1.0)
    )


def _sequence(transition, origin=Origin.CENTER):
    return (
        VSceneSequence()
        .scene(_moving("#402020", origin), 0.4)
        .transition(transition)
        .scene(_moving("#204020", origin), 0.4)
    )


TRANSITIONS = [
    Fade(duration=0.4),
    Fade(duration=0.4, easing=easing.in_out, overlapping=True),
    Iris(direction="open", duration=0.4),
    Iris(direction="close", duration=0.4, center=(30, -20)),
    *[Slide(direction=d, duration=0.4) for d in ("left", "right", "up", "down")],
    *[Wipe(direction=d, duration=0.4, overlapping=True) for d in ("left", "right", "up", "down")],
    Zoom(direction="in", duration=0.4),
    Zoom(direction="out", duration=0.4, max_scale=3.0),
]


@pytest.mark.integration
@pytest.mark.parametrize("transition", TRANSITIONS, ids=repr)
@pytest.mark.parametrize("t", [0.1, 0.35, 0.5, 0.65, 0.95])
def test_transition(tmp_path, transition, t):
    assert_matches_resvg(_sequence(transition), tmp_path, t=t)


@pytest.mark.integration
@pytest.mark.parametrize("transition", [
    Iris(direction="open", duration=0.4),
    Wipe(direction="left", duration=0.4),
    Zoom(direction="in", duration=0.4),
], ids=repr)
def test_transition_top_left_at_twice_the_size(tmp_path, transition):
    sequence = _sequence(transition, Origin.TOP_LEFT)
    assert_matches_resvg(sequence, tmp_path, t=0.5, w=2 * W, h=2 * H)


@pytest.mark.integration
def test_transition_keeps_a_scenes_clip(tmp_path):
    clipped = _scene().add_element(VElement(state=_rect(clip_state=CircleState(radius=50))))
    sequence = (
        VSceneSequence()
        .scene(clipped, 0.4)
        .transition(Fade(duration=0.4))
        .scene(_moving("#204020"), 0.4)
    )
    assert_matches_resvg(sequence, tmp_path, t=0.4)


@pytest.mark.integration
@pytest.mark.parametrize("t", [0.2, 0.5, 0.8])
def test_sequence_and_composite_nest_both_ways(tmp_path, t):
    inner = VSceneSequence().scene(_small("#aa2222"), 0.4).transition(
        Wipe(duration=0.2)).scene(_small("#2222aa"), 0.4)
    row = VSceneComposite([inner, _small("#22aa22")], direction="horizontal")
    outer = VSceneSequence(width=row.width, height=row.height).scene(
        row, 0.5).transition(Fade(duration=0.2)).scene(
        VSceneComposite([_small("#555555"), inner], direction="horizontal"), 0.5)
    assert_matches_resvg(outer, tmp_path, t=t, w=int(row.width), h=int(row.height))


@pytest.mark.unit
def test_transition_without_skia_version_is_reported():
    from svan2d.transition.scene.base import SceneTransition

    class Custom(SceneTransition):
        def composite(self, scene_out, scene_in, progress, time_out, time_in, ctx):
            raise NotImplementedError

    sequence = VSceneSequence().scene(_moving("#000"), 0.5).transition(
        Custom(duration=0.2)).scene(_moving("#111"), 0.5)
    assert check_scene(sequence) == ["no Skia version of transition Custom"]


# --------------------------------------------------------------------------
# Image opacity
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_image_opacity_is_written_once(tmp_path):
    from svan2d.primitive.state.image import ImageState

    white = tmp_path / "white.png"
    surface = skia.Surface(20, 20)
    surface.getCanvas().clear(skia.ColorWHITE)
    surface.makeImageSnapshot().save(str(white), skia.kPNG)
    svg = VScene(width=100, height=100).add_element(
        VElement(state=ImageState(href=str(white), width=80, height=80, opacity=0.5))
    ).to_svg(log=False)
    assert svg.count('opacity="0.5"') == 1


@pytest.mark.integration
def test_image_opacity_applies_once(tmp_path):
    from svan2d.primitive.state.image import ImageState

    white = tmp_path / "white.png"
    surface = skia.Surface(20, 20)
    surface.getCanvas().clear(skia.ColorWHITE)
    surface.makeImageSnapshot().save(str(white), skia.kPNG)
    scene = _scene().add_element(
        VElement(state=ImageState(href=str(white), width=80, height=80, opacity=0.5))
    )
    assert_matches_resvg(scene, tmp_path)
    for converter in (SkiaSvgConverter(), ResvgSvgConverter()):
        centre = _png(converter, scene, tmp_path, "centre.png", 0.0, W, H)[H // 2, W // 2]
        # Half of white over the #102030 background.
        assert abs(centre[0] - (255 + 0x10) / 2) <= 2, (type(converter).__name__, centre)


# --------------------------------------------------------------------------
# Group easing
# --------------------------------------------------------------------------


def _moving_child(y=0):
    return (
        VElement()
        .keystate(CircleState(radius=15, pos=Point2D(-70, y), fill_color=Color("#ffffff")), at=0.0)
        .keystate(CircleState(radius=15, pos=Point2D(70, y), fill_color=Color("#ffffff")), at=1.0)
    )


@pytest.mark.integration
@pytest.mark.parametrize("own_keystate", [True, False])
@pytest.mark.parametrize("t", [0.3, 0.6, 0.9])
def test_group_easing(tmp_path, own_keystate, t):
    from svan2d.transition import easing

    group = VElementGroup(elements=[_moving_child()], group_easing=easing.in_cubic)
    if own_keystate:
        group = group.keystate(VElementGroupState())
    assert_matches_resvg(_scene().add_element(group), tmp_path, t=t)


@pytest.mark.integration
@pytest.mark.parametrize("t", [0.3, 0.7])
def test_nested_group_easing(tmp_path, t):
    from svan2d.transition import easing

    inner = VElementGroup(elements=[_moving_child(30)], group_easing=easing.out_cubic)
    outer = VElementGroup(elements=[inner, _moving_child(-30)], group_easing=easing.in_cubic)
    assert_matches_resvg(_scene().add_element(outer), tmp_path, t=t)
