"""Bar Chart Race Animation — Global EV Sales by Country (2010–2023).

Animated bar chart showing electric vehicle sales by country over time.
Data source: IEA Global EV Data 2024.
"""

import tomllib
from pathlib import Path

from axis import create_axis_elements, AxisConfig
from bar import create_bar_elements, BarConfig, estimate_label_reserve
from data_prep import get_company_data, InterpolationMethod
from year import create_year_element

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.vscene.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter

configure_logging(level="INFO")


# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.toml"
with open(CONFIG_PATH, "rb") as f:
    cfg = tomllib.load(f)


def calculate_layout(cfg: dict) -> dict:
    """Calculate plot bounds and bar dimensions from scene size and margins."""
    width = cfg["scene"]["width"]
    height = cfg["scene"]["height"]
    top_n = cfg["data"]["top_n"]

    plot_left = -width / 2 + cfg["layout"]["margin_left"]
    plot_right = width / 2 - cfg["layout"]["margin_right"]
    plot_top = -height / 2 + cfg["layout"]["margin_top"]
    plot_bottom = height / 2 - cfg["layout"]["margin_bottom"]

    plot_height = plot_bottom - plot_top
    bar_slot = plot_height / top_n
    bar_margin = max(2, bar_slot * 0.12)
    bar_height = bar_slot - bar_margin

    return {
        "plot_left": plot_left,
        "plot_right": plot_right,
        "plot_top": plot_top,
        "plot_bottom": plot_bottom,
        "bar_height": bar_height,
        "bar_margin": bar_margin,
        "bar_slot": bar_slot,
    }


def get_category_colors(
    company_data: dict, palette_override: list[str] | None = None
) -> dict[str, Color]:
    """Map colors to categories based on final frame ranking."""
    palette = palette_override or cfg["bars"]["palette"]

    final_values = {}
    for company_name, data_points in company_data.items():
        final_point = data_points[-1]
        category = final_point.category
        if category not in final_values or final_point.value > final_values[category]:
            final_values[category] = final_point.value

    sorted_categories = sorted(
        final_values.keys(), key=lambda c: final_values[c], reverse=True
    )

    return {
        category: Color(palette[i % len(palette)])
        for i, category in enumerate(sorted_categories)
    }


def get_max_values_per_frame(company_data: dict) -> list[float]:
    """Extract maximum value for each frame across all countries."""
    first_company_data = next(iter(company_data.values()))
    num_frames = len(first_company_data)

    return [
        max(data_points[i].value for data_points in company_data.values())
        for i in range(num_frames)
    ]


def create_scene() -> VScene:
    layout = calculate_layout(cfg)

    scene = VScene(
        width=cfg["scene"]["width"],
        height=cfg["scene"]["height"],
        background=Color(cfg["scene"]["background"]),
    )

    company_data = get_company_data(
        data_path=cfg["data"]["path"],
        top_n=cfg["data"]["top_n"],
        interpolated_data_per_year=cfg["data"]["interpolated_points_per_year"],
        interpolation_method=InterpolationMethod.PCHIP,
    )

    category_colors = get_category_colors(company_data)

    label_reserve = estimate_label_reserve(
        company_data,
        name_font_size=cfg["bars"]["name_size"],
        value_font_size=cfg["bars"]["value_size"],
        label_gap=cfg["bars"]["label_gap"],
    )

    bar_config = BarConfig(
        plot_left=layout["plot_left"],
        plot_right=layout["plot_right"],
        plot_top=layout["plot_top"],
        plot_bottom=layout["plot_bottom"],
        bar_height=layout["bar_height"],
        bar_margin=layout["bar_margin"],
        top_n=cfg["data"]["top_n"],
        fill_opacity=cfg["bars"]["fill_opacity"],
        name_font_family=cfg["bars"]["name_family"],
        name_font_size=cfg["bars"]["name_size"],
        name_font_weight=cfg["bars"]["name_weight"],
        name_color=Color(cfg["bars"]["name_color"]),
        value_font_family=cfg["bars"]["value_family"],
        value_font_size=cfg["bars"]["value_size"],
        value_font_weight=cfg["bars"]["value_weight"],
        value_color=Color(cfg["bars"]["value_color"]),
        label_gap=cfg["bars"]["label_gap"],
        label_reserve=label_reserve,
    )

    bar_elements, name_elements, value_elements = create_bar_elements(
        company_data, category_colors, bar_config
    )
    scene = scene.add_elements(bar_elements)
    scene = scene.add_elements(name_elements)
    scene = scene.add_elements(value_elements)

    max_values = get_max_values_per_frame(company_data)
    bar_slot = layout["bar_slot"]
    bar_height = layout["bar_height"]
    first_bar_top = layout["plot_top"] + 0.5 * bar_slot - bar_height / 2
    last_bar_bottom = (
        layout["plot_top"] + (cfg["data"]["top_n"] - 0.5) * bar_slot + bar_height / 2
    )

    axis_config = AxisConfig(
        left_x=layout["plot_left"],
        width=layout["plot_right"] - layout["plot_left"],
        label_y=first_bar_top - cfg["axis"]["label_offset"],
        line_top_y=first_bar_top,
        line_height=last_bar_bottom - first_bar_top,
        target_tick_count=cfg["axis"]["target_tick_count"],
        font_family=cfg["axis"]["family"],
        font_size=cfg["axis"]["size"],
        label_color=Color(cfg["axis"]["label_color"]),
        line_color=Color(cfg["axis"]["line_color"]),
        line_opacity=1.0,
        zero_line_color=Color(cfg["axis"]["zero_line_color"]),
        zero_line_width=cfg["axis"]["zero_line_width"],
    )
    axis_elements = create_axis_elements(max_values, axis_config)
    scene = scene.add_elements(axis_elements)

    year_element = create_year_element(
        company_data,
        layout,
        font_family=cfg["year"]["family"],
        font_size=cfg["year"]["size"],
        fill_color=Color(cfg["year"]["color"]),
        fill_opacity=cfg["year"]["opacity"],
        offset_right=cfg["year"]["offset_right"],
        offset_bottom=cfg["year"]["offset_bottom"],
    )
    scene = scene.add_element(year_element)

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
        total_frames=cfg["export"]["total_frames"],
        framerate=cfg["export"]["framerate"],
        png_width_px=cfg["export"]["png_width_px"],
        parallel_workers=(
            4 if ConverterType(cfg["export"]["converter"]) == "playwright_http" else 1
        ),
    )
