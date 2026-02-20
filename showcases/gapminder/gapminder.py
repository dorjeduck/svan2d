"""Gapminder Bubble Chart Animation.

Hans Rosling-style animated bubble chart showing the relationship between
GDP per capita, life expectancy, and population across countries over time.
"""

import tomllib
from pathlib import Path

from axis import create_axis_elements, AxisConfig
from bubble import create_bubble_elements, BubbleConfig
from data_prep import get_country_data
from legend import create_legend_elements, LegendConfig
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
    """Calculate plot bounds from scene size and margins."""
    width = cfg["scene"]["width"]
    height = cfg["scene"]["height"]

    plot_left = -width / 2 + cfg["layout"]["margin_left"]
    plot_right = width / 2 - cfg["layout"]["margin_right"]
    plot_top = -height / 2 + cfg["layout"]["margin_top"]
    plot_bottom = height / 2 - cfg["layout"]["margin_bottom"]

    return {
        "plot_left": plot_left,
        "plot_right": plot_right,
        "plot_top": plot_top,
        "plot_bottom": plot_bottom,
    }


def get_continent_colors(cfg: dict) -> dict[str, Color]:
    """Build continent → Color mapping from config."""
    return {
        continent: Color(hex_color)
        for continent, hex_color in cfg["bubbles"]["continent_colors"].items()
    }


def get_labeled_countries(
    country_data: dict, cfg: dict
) -> set[str]:
    """Determine which countries get text labels.

    Uses top N by max population across all years.
    """
    top_n = cfg["labels"]["top_n"]

    # Find max population per country
    max_pops = {}
    for country_name, data_points in country_data.items():
        max_pops[country_name] = max(p.population for p in data_points)

    sorted_countries = sorted(max_pops, key=lambda c: max_pops[c], reverse=True)
    return set(sorted_countries[:top_n])


def create_scene() -> VScene:
    layout = calculate_layout(cfg)

    scene = VScene(
        width=cfg["scene"]["width"],
        height=cfg["scene"]["height"],
        background=Color(cfg["scene"]["background"]),
    )

    # Load data
    col_cfg = cfg["data"]["columns"]
    column_map = {
        col_cfg["life_exp"]: "life_exp",
        col_cfg["gdp_per_cap"]: "gdp_per_cap",
        col_cfg["population"]: "population",
    }

    country_data = get_country_data(
        data_path=cfg["data"]["path"],
        top_n=cfg["data"]["top_n"],
        column_map=column_map,
    )

    # Colors
    continent_colors = get_continent_colors(cfg)
    labeled_countries = get_labeled_countries(country_data, cfg)

    # Bubble config
    bcfg = cfg["bubbles"]
    acfg = cfg["axes"]
    bubble_config = BubbleConfig(
        plot_left=layout["plot_left"],
        plot_right=layout["plot_right"],
        plot_top=layout["plot_top"],
        plot_bottom=layout["plot_bottom"],
        gdp_min=acfg["gdp_min"],
        gdp_max=acfg["gdp_max"],
        life_exp_min=acfg["life_exp_min"],
        life_exp_max=acfg["life_exp_max"],
        radius_min=bcfg["radius_min"],
        radius_max=bcfg["radius_max"],
        radius_reference_pop=bcfg["radius_reference_pop"],
        fill_opacity=bcfg["fill_opacity"],
        stroke_color=Color(bcfg["stroke_color"]),
        stroke_width=bcfg["stroke_width"],
        stroke_opacity=bcfg["stroke_opacity"],
        label_font_family=cfg["labels"]["font_family"],
        label_font_size=cfg["labels"]["font_size"],
        label_font_weight=cfg["labels"]["font_weight"],
        label_color=Color(cfg["labels"]["color"]),
        label_offset_y=cfg["labels"]["offset_y"],
    )

    # Create bubble + label elements
    bubble_elements, label_elements = create_bubble_elements(
        country_data, continent_colors, bubble_config, labeled_countries
    )
    scene = scene.add_elements(bubble_elements)
    scene = scene.add_elements(label_elements)

    # Create axes
    axis_config = AxisConfig(
        gdp_ticks=acfg["gdp_ticks"],
        life_exp_ticks=acfg["life_exp_ticks"],
        gridline_color=Color(acfg["gridline_color"]),
        gridline_width=acfg["gridline_width"],
        gridline_opacity=acfg["gridline_opacity"],
        border_color=Color(acfg["border_color"]),
        border_width=acfg["border_width"],
        font_family=acfg["font_family"],
        font_size=acfg["font_size"],
        label_color=Color(acfg["label_color"]),
        title_font_family=acfg["title_font_family"],
        title_font_size=acfg["title_font_size"],
        title_font_weight=acfg["title_font_weight"],
        title_color=Color(acfg["title_color"]),
        x_title=acfg["x_title"],
        y_title=acfg["y_title"],
    )
    axis_elements = create_axis_elements(bubble_config, axis_config)
    scene = scene.add_elements(axis_elements)

    # Create year display
    ycfg = cfg["year"]
    year_element = create_year_element(
        country_data,
        layout,
        font_family=ycfg["font_family"],
        font_size=ycfg["font_size"],
        font_weight=ycfg["font_weight"],
        fill_color=Color(ycfg["color"]),
        fill_opacity=ycfg["opacity"],
        offset_right=ycfg["offset_right"],
        offset_bottom=ycfg["offset_bottom"],
    )
    scene = scene.add_element(year_element)

    # Create legend
    lcfg = cfg["legend"]
    legend_config = LegendConfig(
        offset_right=lcfg["offset_right"],
        offset_top=lcfg["offset_top"],
        swatch_radius=lcfg["swatch_radius"],
        swatch_gap=lcfg["swatch_gap"],
        label_offset_x=lcfg["label_offset_x"],
        font_family=lcfg["font_family"],
        font_size=lcfg["font_size"],
        font_color=Color(lcfg["font_color"]),
    )
    legend_elements = create_legend_elements(
        continent_colors,
        layout["plot_right"],
        layout["plot_top"],
        legend_config,
    )
    scene = scene.add_elements(legend_elements)

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
