"""Tests for the Skia canvas rendering backend.

Covers: registry resolution, the one-time capability scan (check_scene),
PNG rendering, faithful geometry (triangle apex-up), and the
stop-with-detail behaviour on unsupported scenes.
"""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")
skia = pytest.importorskip("skia")

from svan2d.core import Color
from svan2d.velement import VElement
from svan2d.vscene import VScene
from svan2d.primitive.state.circle import CircleState
from svan2d.primitive.state.rectangle import RectangleState
from svan2d.primitive.state.square import SquareState
from svan2d.primitive.state.triangle import TriangleState
from svan2d.primitive.state.text import TextState
from svan2d.primitive.effect.filter.gaussian_blur import GaussianBlurFilter

from svan2d.converter.skia_svg_converter import SkiaSvgConverter
from svan2d.skia import check_scene, SkiaUnsupported
from svan2d.primitive.registry import get_skia_renderer_class_for_state
from svan2d.primitive.renderer.skia import (
    CircleSkiaRenderer,
    RectangleSkiaRenderer,
    TriangleSkiaRenderer,
)


def _render(scene: VScene, tmp_path, w=200, h=200, name="out.png"):
    out = str(tmp_path / name)
    res = SkiaSvgConverter()._convert_to_png(scene, out, 0.0, w, h)
    assert res["success"], res
    return skia.Image.open(out).toarray()  # H x W x 4, RGBA


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_registry_resolves_builtin_renderers():
    assert get_skia_renderer_class_for_state(CircleState(radius=1)) is CircleSkiaRenderer
    assert get_skia_renderer_class_for_state(RectangleState(width=1, height=1)) is RectangleSkiaRenderer
    assert get_skia_renderer_class_for_state(TriangleState(size=1)) is TriangleSkiaRenderer


@pytest.mark.unit
def test_subclass_inherits_via_mro():
    # SquareState has its own renderer; resolution must not fall through to a base.
    from svan2d.primitive.renderer.skia import SquareSkiaRenderer

    assert get_skia_renderer_class_for_state(SquareState(size=1)) is SquareSkiaRenderer


# --------------------------------------------------------------------------
# Capability scan
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_check_scene_supported_is_empty():
    scene = VScene(width=100, height=100).add_elements(
        [
            VElement(state=CircleState(radius=10, fill_color=Color("#fff"))),
            VElement(state=TriangleState(size=10, fill_color=Color("#f00"))),
        ]
    )
    assert check_scene(scene) == []


@pytest.mark.unit
def test_check_scene_reports_filter():
    scene = VScene(width=100, height=100).add_element(
        VElement(state=CircleState(radius=10, fill_color=Color("#fff"),
                                   filter=GaussianBlurFilter(std_deviation=2)))
    )
    reasons = check_scene(scene)
    assert any("filter" in r for r in reasons)


@pytest.mark.unit
def test_check_scene_reports_unregistered_primitive():
    # PathVariantsState's Skia renderer is attached per-element (carrying a
    # variant), so the bare base state resolves to no registry renderer.
    from svan2d.primitive.state.path_variants import PathVariantsState

    scene = VScene(width=100, height=100).add_element(
        VElement(state=PathVariantsState())
    )
    reasons = check_scene(scene)
    assert any("PathVariantsState" in r and "no Skia renderer" in r for r in reasons)


@pytest.mark.unit
def test_path_text_resolves_and_renders(tmp_path):
    from svan2d.primitive.state.path_text import PathTextState
    from svan2d.primitive.renderer.skia import PathTextSkiaRenderer

    state = PathTextState(text="HELLO", data="M -80,0 L 80,0", fill_color=Color("black"))
    assert get_skia_renderer_class_for_state(state) is PathTextSkiaRenderer
    scene = VScene(width=200, height=200).add_element(VElement(state=state))
    assert check_scene(scene) == []
    arr = _render(scene, tmp_path, 200, 200, name="path_text.png")
    # Some black text pixels must have been drawn.
    assert (arr[..., :3].sum(axis=-1) < 200).any()


@pytest.mark.unit
def test_circle_text_resolves_and_renders(tmp_path):
    from svan2d.primitive.state.circle_text import CircleTextState
    from svan2d.primitive.renderer.skia import CircleTextSkiaRenderer

    state = CircleTextState(text="AROUND", radius=60, fill_color=Color("black"))
    assert get_skia_renderer_class_for_state(state) is CircleTextSkiaRenderer
    scene = VScene(width=200, height=200).add_element(VElement(state=state))
    assert check_scene(scene) == []
    arr = _render(scene, tmp_path, 200, 200, name="circle_text.png")
    assert (arr[..., :3].sum(axis=-1) < 200).any()


@pytest.mark.unit
def test_raw_svg_resolves_to_dedicated():
    from svan2d.primitive.state.raw_svg import RawSvgState
    from svan2d.primitive.renderer.skia import RawSvgSkiaRenderer

    state = RawSvgState(svg_data="<rect/>")
    assert get_skia_renderer_class_for_state(state) is RawSvgSkiaRenderer
    # A scene of only raw_svg is now fully supported by Skia.
    scene = VScene(width=100, height=100).add_element(VElement(state=state))
    assert check_scene(scene) == []


@pytest.mark.integration
def test_raw_svg_renders_fragment(tmp_path):
    # Best-effort SVGDOM render: a solid rect fragment must produce its pixels.
    from svan2d.primitive.state.raw_svg import RawSvgState
    from svan2d.core.enums import Origin

    frag = '<rect x="0" y="0" width="60" height="60" fill="#ff0000"/>'
    scene = VScene(width=100, height=100, origin=Origin.TOP_LEFT).add_element(
        VElement(state=RawSvgState(svg_data=frag))
    )
    arr = _render(scene, tmp_path, 100, 100, name="raw.png")
    # Red pixels somewhere in the top-left quadrant.
    red = (arr[:60, :60, 0] > 200) & (arr[:60, :60, 1] < 60)
    assert red.sum() > 1000


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_renders_valid_png_of_requested_size(tmp_path):
    scene = VScene(width=200, height=200, background=Color("#000000")).add_element(
        VElement(state=CircleState(radius=50, fill_color=Color("#ffffff")))
    )
    arr = _render(scene, tmp_path)
    assert arr.shape[0] == 200 and arr.shape[1] == 200


@pytest.mark.integration
def test_circle_fill_color_at_center(tmp_path):
    scene = VScene(width=200, height=200, background=Color("#000000")).add_element(
        VElement(state=CircleState(radius=60, fill_color=Color("#ff0000")))
    )
    arr = _render(scene, tmp_path)
    cx, cy = 100, 100
    r, g, b = arr[cy, cx, 0], arr[cy, cx, 1], arr[cy, cx, 2]
    assert r > 200 and g < 60 and b < 60  # red center
    # corner is background (black)
    assert arr[5, 5, 0] < 40


@pytest.mark.integration
def test_triangle_points_up(tmp_path):
    # Faithful to TriangleRenderer: apex at top, base at bottom.
    scene = VScene(width=200, height=200, background=Color("#000000")).add_element(
        VElement(state=TriangleState(size=80, fill_color=Color("#ffffff")))
    )
    arr = _render(scene, tmp_path)
    # Near the apex (top, on the vertical centerline) the triangle is narrow:
    # a point just below the top vertex is filled; the bottom corners are filled
    # while the bottom-center-outside stays background.
    top_filled = arr[40, 100, 0] > 200      # just below apex, centerline
    bottom_left = arr[135, 70, 0] > 200      # bottom-left region
    bottom_right = arr[135, 130, 0] > 200    # bottom-right region
    apex_sides_empty = arr[40, 60, 0] < 40   # left of the narrow apex = bg
    assert top_filled and bottom_left and bottom_right and apex_sides_empty


@pytest.mark.integration
def test_path_with_arc_renders(tmp_path):
    # A filled circle described with arc commands (exercises the arc parser fix
    # + PathSkiaRenderer). Center filled, just-outside is background.
    from svan2d.primitive.state.path import PathState

    circle = "M0,0 m-50,0 a50,50 0 1,0 100,0 a50,50 0 1,0 -100,0"
    scene = VScene(width=200, height=200, background=Color("#000000")).add_element(
        VElement(state=PathState(data=circle, fill_color=Color("#ffffff")))
    )
    arr = _render(scene, tmp_path)
    assert arr[100, 100, 0] > 200   # center filled (white)
    assert arr[100, 5, 0] < 40      # far left = background


@pytest.mark.integration
def test_text_renders_without_error(tmp_path):
    scene = VScene(width=300, height=120, background=Color("#000000")).add_element(
        VElement(state=TextState(text="Skia", font_size=48, fill_color=Color("#ffffff")))
    )
    arr = _render(scene, tmp_path, w=300, h=120)
    # Some white pixels exist (text was drawn).
    assert (arr[:, :, 0] > 200).sum() > 50


# --------------------------------------------------------------------------
# Stop-with-detail
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Native curve renderers (arc / ring / astroid) — registry + fidelity vs SVG
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_curve_renderers_resolve_to_dedicated():
    from svan2d.primitive.state.arc import ArcState
    from svan2d.primitive.state.ring import RingState
    from svan2d.primitive.state.astroid import AstroidState
    from svan2d.primitive.renderer.skia import (
        ArcSkiaRenderer,
        RingSkiaRenderer,
        AstroidSkiaRenderer,
    )

    assert get_skia_renderer_class_for_state(ArcState()) is ArcSkiaRenderer
    assert get_skia_renderer_class_for_state(RingState()) is RingSkiaRenderer
    assert get_skia_renderer_class_for_state(AstroidState()) is AstroidSkiaRenderer


def _resvg_render(scene, tmp_path, w, h, name):
    from svan2d.converter.resvg_svg_converter import ResvgSvgConverter

    out = str(tmp_path / name)
    res = ResvgSvgConverter()._convert_to_png(scene, out, 0.0, w, h)
    assert res["success"], res
    return skia.Image.open(out).toarray()


@pytest.mark.integration
@pytest.mark.parametrize("state_factory", [
    lambda: __import__("svan2d.primitive.state.arc", fromlist=["ArcState"]).ArcState(
        radius=70, start_angle=20, end_angle=200, stroke_color=Color("#fff"), stroke_width=6),
    lambda: __import__("svan2d.primitive.state.ring", fromlist=["RingState"]).RingState(
        outer_radius=80, inner_radius=40, fill_color=Color("#fff")),
    lambda: __import__("svan2d.primitive.state.astroid", fromlist=["AstroidState"]).AstroidState(
        radius=80, num_cusps=4, curvature=0.7, fill_color=Color("#fff")),
])
def test_native_curve_matches_resvg(tmp_path, state_factory):
    # The native Skia curve renderer must reproduce the SVG (resvg) output,
    # not approximate it with a polyline.
    state = state_factory()
    scene = VScene(width=200, height=200, background=Color("#000000")).add_element(
        VElement(state=state)
    )
    skia_arr = _render(scene, tmp_path, name="skia.png")
    resvg_arr = _resvg_render(scene, tmp_path, 200, 200, "resvg.png")

    # Compare luminance; allow a thin antialiased edge band to differ.
    diff = np.abs(skia_arr[:, :, 0].astype(int) - resvg_arr[:, :, 0].astype(int))
    differing = (diff > 60).mean()
    assert differing < 0.02, f"{differing:.3%} pixels differ — not faithful to SVG"


# --------------------------------------------------------------------------
# path_band / radial_segments / number / text_path renderers
# --------------------------------------------------------------------------


def _find_font() -> str | None:
    import os

    for p in (
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if os.path.exists(p):
            return p
    return None


@pytest.mark.unit
def test_new_renderers_resolve_to_dedicated():
    from svan2d.core.point2d import Point2D
    from svan2d.primitive.state.path_band import PathBandState
    from svan2d.primitive.state.radial_segments import RadialSegmentsState
    from svan2d.primitive.state.number import NumberState
    from svan2d.primitive.state.text_path import TextPathState
    from svan2d.primitive.renderer.skia import (
        PathBandSkiaRenderer,
        RadialSegmentsSkiaRenderer,
        NumberSkiaRenderer,
        TextPathSkiaRenderer,
    )

    pb = PathBandState(segments=((Point2D(0, 0), Point2D(1, 1)),))
    assert get_skia_renderer_class_for_state(pb) is PathBandSkiaRenderer
    assert get_skia_renderer_class_for_state(RadialSegmentsState()) is RadialSegmentsSkiaRenderer
    # NumberState subclasses TextState but resolves to its own renderer (not TextSkiaRenderer).
    assert get_skia_renderer_class_for_state(NumberState(value=1.0)) is NumberSkiaRenderer
    tp = TextPathState(text="x", font_path="/x.ttf")
    assert get_skia_renderer_class_for_state(tp) is TextPathSkiaRenderer


@pytest.mark.unit
def test_check_scene_reports_pathband_gradient():
    from svan2d.core.point2d import Point2D
    from svan2d.primitive.state.path_band import PathBandState
    from svan2d.primitive.effect.gradient.linear import LinearGradient
    from svan2d.primitive.effect.gradient.gradient_stop import GradientStop

    grad = LinearGradient(
        start=Point2D(0, 0),
        end=Point2D(10, 0),
        stops=(GradientStop(0.0, Color("#fff")), GradientStop(1.0, Color("#000"))),
    )
    seg = (Point2D(0, 0), Point2D(10, 0))
    state = PathBandState(segments=(seg,), stroke_gradients=(grad,), stroke_width=2)
    reasons = check_scene(
        VScene(width=50, height=50).add_element(VElement(state=state))
    )
    assert any("gradient" in r for r in reasons)


@pytest.mark.integration
@pytest.mark.parametrize("state_factory", [
    lambda: __import__("svan2d.primitive.state.path_band", fromlist=["PathBandState"]).PathBandState(
        segments=(
            (__import__("svan2d.core.point2d", fromlist=["Point2D"]).Point2D(-80, -40),
             __import__("svan2d.core.point2d", fromlist=["Point2D"]).Point2D(80, 40)),
            (__import__("svan2d.core.point2d", fromlist=["Point2D"]).Point2D(-60, 60),
             __import__("svan2d.core.point2d", fromlist=["Point2D"]).Point2D(60, -60)),
        ),
        stroke_color=Color("#fff"), stroke_width=5),
    lambda: __import__("svan2d.primitive.state.radial_segments", fromlist=["RadialSegmentsState"]).RadialSegmentsState(
        num_lines=16, segments=[(30, 85)], stroke_color=Color("#fff"), stroke_width=3),
])
def test_pathband_radial_match_resvg(tmp_path, state_factory):
    scene = VScene(width=200, height=200, background=Color("#000000")).add_element(
        VElement(state=state_factory())
    )
    skia_arr = _render(scene, tmp_path, name="skia.png")
    resvg_arr = _resvg_render(scene, tmp_path, 200, 200, "resvg.png")
    diff = np.abs(skia_arr[:, :, 0].astype(int) - resvg_arr[:, :, 0].astype(int))
    assert (diff > 60).mean() < 0.02


@pytest.mark.integration
def test_text_path_matches_resvg(tmp_path):
    font = _find_font()
    if font is None:
        pytest.skip("no system font available")
    from svan2d.primitive.state.text_path import TextPathState

    scene = VScene(width=300, height=150, background=Color("#000000")).add_element(
        VElement(state=TextPathState(text="Ag", font_path=font, font_size=80,
                                     fill_color=Color("#ffffff")))
    )
    skia_arr = _render(scene, tmp_path, w=300, h=150, name="skia.png")
    resvg_arr = _resvg_render(scene, tmp_path, 300, 150, "resvg.png")
    diff = np.abs(skia_arr[:, :, 0].astype(int) - resvg_arr[:, :, 0].astype(int))
    assert (diff > 60).mean() < 0.02


@pytest.mark.integration
def test_number_aligned_renders(tmp_path):
    from svan2d.primitive.state.number import NumberState, NumberFormat

    scene = VScene(width=300, height=120, background=Color("#000000")).add_element(
        VElement(state=NumberState(value=12.34, format=NumberFormat.FIXED_ALIGNED,
                                   decimals=2, font_size=48, fill_color=Color("#ffffff")))
    )
    arr = _render(scene, tmp_path, w=300, h=120)
    assert (arr[:, :, 0] > 200).sum() > 50


# --------------------------------------------------------------------------
# PathVariants: per-element Skia renderer carrying a variant
# --------------------------------------------------------------------------

from dataclasses import dataclass

from svan2d.primitive import PathVariantsRenderer, PathVariantsState
from svan2d.primitive.renderer.skia import PathVariantsSkiaRenderer

_SQUARE_VARIANTS = {
    "square": {"path": "M10,10 L50,10 L50,50 L10,50 Z", "viewbox": 60, "center": (30, 30)},
}


@dataclass(frozen=True)
class _DemoState(PathVariantsState):
    pass


class _DemoRenderer(PathVariantsRenderer):
    PATH_VARIANTS = _SQUARE_VARIANTS


class _DemoSkiaRenderer(PathVariantsSkiaRenderer):
    PATH_VARIANTS = _SQUARE_VARIANTS


def _demo_element():
    state = _DemoState(size=50, fill_color=Color("#ffffff"))
    return (
        VElement(state=state, renderer=_DemoRenderer(variant="square"))
        .skia_renderer(_DemoSkiaRenderer(variant="square"))
    )


@pytest.mark.unit
def test_path_variants_element_renderer_makes_scene_supported():
    # The state alone has no Skia renderer (resolves to None via MRO), but an
    # explicit per-element _skia_renderer must make check_scene pass.
    from svan2d.primitive.state.path_variants import PathVariantsState as _PVS

    assert get_skia_renderer_class_for_state(_PVS()) is None
    scene = VScene(width=100, height=100).add_element(_demo_element())
    assert check_scene(scene) == []


@pytest.mark.integration
def test_path_variants_matches_resvg(tmp_path):
    scene = VScene(width=100, height=100, background=Color("#000000")).add_element(
        _demo_element()
    )
    skia_arr = _render(scene, tmp_path, 100, 100, name="skia.png")
    resvg_arr = _resvg_render(scene, tmp_path, 100, 100, "resvg.png")
    diff = np.abs(skia_arr[:, :, 0].astype(int) - resvg_arr[:, :, 0].astype(int))
    assert (skia_arr[:, :, 0] > 200).sum() > 500
    assert (diff > 60).mean() < 0.02


# --------------------------------------------------------------------------
# PathAndTextVariants: path + text label per-element renderer
# --------------------------------------------------------------------------

from svan2d.primitive import PathAndTextVariantsRenderer, PathAndTextVariantsState
from svan2d.primitive.renderer.skia import PathAndTextVariantsSkiaRenderer

_LABELLED_VARIANTS = {
    "box": {
        "path": "M150,150 L350,150 L350,350 L150,350 Z",
        "text": "BOX",
        "text_position": (200, 420),
        "viewbox": 500,
        "center": (250, 250),
    },
}


@dataclass(frozen=True)
class _LabelState(PathAndTextVariantsState):
    pass


class _LabelRenderer(PathAndTextVariantsRenderer):
    PATH_VARIANTS = _LABELLED_VARIANTS


class _LabelSkiaRenderer(PathAndTextVariantsSkiaRenderer):
    PATH_VARIANTS = _LABELLED_VARIANTS


def _label_element():
    state = _LabelState(size=400, fill_color=Color("#ffffff"), text_color=Color("#ffffff"))
    return (
        VElement(state=state, renderer=_LabelRenderer(variant="box"))
        .skia_renderer(_LabelSkiaRenderer(variant="box"))
    )


@pytest.mark.unit
def test_path_and_text_variants_element_renderer_makes_scene_supported():
    scene = VScene(width=300, height=300).add_element(_label_element())
    assert check_scene(scene) == []


@pytest.mark.integration
def test_path_and_text_variants_matches_resvg(tmp_path):
    scene = VScene(width=300, height=300, background=Color("#000000")).add_element(
        _label_element()
    )
    skia_arr = _render(scene, tmp_path, 300, 300, name="skia.png")
    resvg_arr = _resvg_render(scene, tmp_path, 300, 300, "resvg.png")
    diff = np.abs(skia_arr[:, :, 0].astype(int) - resvg_arr[:, :, 0].astype(int))
    # Square is exact; text glyph metrics differ slightly between Skia and resvg.
    assert (skia_arr[:, :, 0] > 200).sum() > 500
    assert (diff > 60).mean() < 0.02


@pytest.mark.integration
def test_converter_stops_with_detail_on_unsupported(tmp_path):
    scene = VScene(width=100, height=100).add_element(
        VElement(state=CircleState(radius=10, fill_color=Color("#fff"),
                                   filter=GaussianBlurFilter(std_deviation=2)))
    )
    with pytest.raises(SkiaUnsupported) as exc:
        SkiaSvgConverter()._convert_to_png(scene, str(tmp_path / "x.png"), 0.0, 100, 100)
    assert "filter" in str(exc.value)


# --------------------------------------------------------------------------
# WebP export
# --------------------------------------------------------------------------


def _webp_fourcc(path: str) -> bytes:
    """Return the WebP container fourcc: b'VP8L' (lossless) or b'VP8 ' (lossy)."""
    with open(path, "rb") as f:
        header = f.read(16)
    assert header[:4] == b"RIFF" and header[8:12] == b"WEBP", "not a WebP file"
    return header[12:16]


def _webp_scene() -> VScene:
    return VScene(width=200, height=200, background=Color("#000000")).add_element(
        VElement(state=CircleState(radius=60, fill_color=Color("#ff0000")))
    )


@pytest.mark.integration
def test_skia_webp_lossless_default(tmp_path):
    out = str(tmp_path / "out.webp")
    res = SkiaSvgConverter()._convert_to_webp(_webp_scene(), out, 0.0, 200, 200)
    assert res["success"], res
    assert _webp_fourcc(out) == b"VP8L"  # quality None -> lossless


@pytest.mark.integration
def test_skia_webp_lossy_quality(tmp_path):
    out = str(tmp_path / "out.webp")
    res = SkiaSvgConverter()._convert_to_webp(
        _webp_scene(), out, 0.0, 200, 200, quality=80
    )
    assert res["success"], res
    assert _webp_fourcc(out) == b"VP8 "  # quality < 100 -> lossy


@pytest.mark.integration
def test_export_to_webp_via_exporter(tmp_path):
    from svan2d.vscene import VSceneExporter
    from svan2d.converter.converter_type import ConverterType

    exporter = VSceneExporter(
        _webp_scene(), output_dir=str(tmp_path), converter=ConverterType.SKIA
    )
    path = exporter.to_webp("circle.webp")
    assert path.endswith(".webp")
    assert _webp_fourcc(path) == b"VP8L"


@pytest.mark.unit
def test_non_skia_backend_reports_webp_unsupported():
    from svan2d.converter.cairo_svg_converter import CairoSvgConverter

    res = CairoSvgConverter()._convert_to_webp(_webp_scene(), "x.webp", 0.0, 100, 100)
    assert res["success"] is False
    assert "WebP" in res["error"]
