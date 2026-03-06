"""Periodic Table Discovery Timeline — elements appear by discovery year."""

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cell_element import create_cell_elements
from data_prep import prepare
from elements import CELL_SIZE, table_size
from year_element import create_year_element

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.vscene.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

configure_logging(level="INFO")

CONFIG_PATH = Path(__file__).parent / "config.toml"
with open(CONFIG_PATH, "rb") as f:
    cfg = tomllib.load(f)


def create_scene() -> VScene:
    data = prepare(cfg)

    ccfg = cfg["cell"]
    w, h = table_size()
    scene = VScene(
        width=w,
        height=h,
        background=Color(cfg["scene"]["background"]),
    )

    scene = scene.add_elements(
        create_cell_elements(
            data,
            cell_size=CELL_SIZE,
            fill_opacity=ccfg["fill_opacity"],
            stroke_color=Color(ccfg["stroke_color"]),
            stroke_width=ccfg["stroke_width"],
            stroke_opacity=ccfg["stroke_opacity"],
            font_family=ccfg["font_family"],
            font_weight=ccfg["font_weight"],
            symbol_font_size=ccfg["symbol_font_size"],
            number_font_size=ccfg["number_font_size"],
            number_opacity=ccfg["number_opacity"],
            number_offset=ccfg["number_offset"],
            label_color=Color(ccfg["label_color"]),
        )
    )

    ycfg = cfg["year_label"]
    scene = scene.add_element(
        create_year_element(
            data,
            font_family=ycfg["font_family"],
            font_size=ycfg["font_size"],
            font_weight=ycfg["font_weight"],
            fill_color=Color(ycfg["color"]),
            fill_opacity=ycfg["opacity"],
        )
    )

    return scene


if __name__ == "__main__":
    scene = create_scene()
    exporter = VSceneExporter(
        scene=scene,
        converter=ConverterType(cfg["export"]["converter"]),
        output_dir=cfg["export"]["output_dir"],
    )
    exporter.to_mp4(
        filename=cfg["export"]["filename"],
        total_frames=cfg["animation"]["total_frames"],
        framerate=cfg["animation"]["framerate"],
        png_width_px=cfg["export"]["png_width_px"],
    )
