"""Periodic Table Timeline to Grid — timeline buildup then fly to grid layout."""

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from axis_element import create_axis_elements
from camera import apply_camera, build_camera_funcs
from cell_element import create_cell_elements
from data_prep import prepare
from elements import CELL_SIZE, table_size
from year_element import create_year_element

from svan2d import Color, configure_logging, ConverterType, VScene, VSceneExporter

configure_logging(level="INFO")

CONFIG_PATH = Path(__file__).parent / "config.toml"
with open(CONFIG_PATH, "rb") as f:
    cfg = tomllib.load(f)


def create_scene() -> VScene:
    data = prepare(cfg)

    tlcfg = cfg["timeline"]
    ccfg = cfg["cell"]
    ycfg = cfg["year_label"]
    acfg = cfg["animation"]

    w, h = table_size()
    scene = VScene(
        width=w,
        height=h,
        background=Color(cfg["scene"]["background"]),
    )

    # Cell elements (squares + symbols + numbers) — these drive the camera
    cell_elements = create_cell_elements(
        data,
        cell_size=CELL_SIZE,
        timeline_cell_size=data.tl_cell_size,
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
        buildup_end=acfg["buildup_end"],
    )
    scene = scene.add_elements(cell_elements)

    # Axis line + tick marks + tick labels — decorative, excluded from camera
    axis_elements = create_axis_elements(
        data,
        axis_color=Color(tlcfg["axis_color"]),
        axis_width=tlcfg["axis_width"],
        tick_height=tlcfg["tick_height"],
        tick_color=Color(tlcfg["tick_color"]),
        tick_font_size=tlcfg["tick_font_size"],
        tick_font_family=tlcfg["tick_font_family"],
        tick_label_color=Color(tlcfg["tick_label_color"]),
        tick_label_offset=tlcfg["tick_label_offset"],
        buildup_end=acfg["buildup_end"],
        fly_end=acfg["fly_end"],
    )
    scene = scene.add_elements(axis_elements)

    # Only cell elements drive camera — axis labels excluded.
    # Sample at settled times (after each cell finishes its scale-up animation)
    # to avoid mid-animation fluctuations in the bounding box.
    # Freeze camera from buildup_end onward so the fly-to-grid phase is stable.
    sample_times = sorted(set(c.t_appear_end for c in data.cells))
    scale_fn, offset_fn = build_camera_funcs(
        scene,
        exclude=axis_elements,
        freeze=[(acfg["buildup_end"], 1.0)],
        sample_times=sample_times,
    )

    # Year label (font size compensated for camera zoom)
    scene = scene.add_element(
        create_year_element(
            data,
            font_family=ycfg["font_family"],
            font_size=ycfg["font_size"],
            font_weight=ycfg["font_weight"],
            fill_color=Color(ycfg["color"]),
            fill_opacity=ycfg["opacity"],
            buildup_end=acfg["buildup_end"],
            fly_end=acfg["fly_end"],
            scale_func=scale_fn,
            offset_func=offset_fn,
        )
    )

    # Camera
    scene = apply_camera(scene, scale_fn, offset_fn)

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
