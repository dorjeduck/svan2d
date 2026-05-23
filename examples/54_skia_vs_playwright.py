"""Skia vs Playwright — Playwright version.

Builds a simple static scene (rounded rect + circle + text label) and renders it
to PNG via the Playwright (HTTP) backend, i.e. the State -> drawsvg -> SVG ->
browser -> PNG pipeline.

Its twin, 54_skia_vs_playwright_skia.py, builds the *same* scene and renders it
through the Skia canvas backend instead. Compare the two PNGs to check the
backends agree visually.

Requires the Playwright render server:  svan2d playwright-server start
"""

from svan2d.core import Color, Point2D, configure_logging
from svan2d.converter import ConverterType
from svan2d.velement import VElement
from svan2d.vscene import VScene, VSceneExporter
from svan2d.primitive.state import CircleState, RectangleState, TextState

configure_logging(level="INFO")


def build_scene() -> VScene:
    """The shared scene — identical in the Skia twin."""
    scene = VScene(width=256, height=256, background=Color("#000017"))

    backdrop = RectangleState(
        pos=Point2D(0, 0),
        width=180,
        height=120,
        corner_radius=16,
        fill_color=Color("#1b3a6b"),
        stroke_color=Color("#FDBE02"),
        stroke_width=3,
    )
    dot = CircleState(
        pos=Point2D(0, -10),
        radius=36,
        fill_color=Color("#FDBE02"),
    )
    label = TextState(
        pos=Point2D(0, 64),
        text="svan2d",
        font_family="Courier New",
        font_size=22,
        fill_color=Color("#FFFFFF"),
    )

    return scene.add_elements(
        [VElement(state=backdrop), VElement(state=dot), VElement(state=label)]
    )


def main():
    scene = build_scene()

    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.PLAYWRIGHT_HTTP,
        output_dir="output/",
    )
    exporter.export(
        filename="54_playwright",
        formats=["png"],
        png_width_px=512,
    )

    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType.SKIA,
        output_dir="output/",
    )
    exporter.export(
        filename="54_skia",
        formats=["png"],
        png_width_px=512,
    )


if __name__ == "__main__":
    main()
