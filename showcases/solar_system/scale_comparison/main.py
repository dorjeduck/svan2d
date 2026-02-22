"""Planet Scale Comparison — planets animate from equal to true relative sizes."""

import sys
import tomllib
from pathlib import Path

# Add shared/ and local directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from planets import get_planets

from elements import (
    create_sun_element,
    create_planet_elements,
    create_label_elements,
)

from svan2d.converter.converter_type import ConverterType
from svan2d.core.color import Color
from svan2d.core.logger import configure_logging
from svan2d.vscene.vscene import VScene
from svan2d.vscene.vscene_exporter import VSceneExporter


def main():
    configure_logging()

    config_path = Path(__file__).parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    # Filter planets
    planet_names = cfg["planets"]["show"]
    planets = get_planets(planet_names)

    # Build elements
    sun_elements = create_sun_element(cfg)
    planet_elements = create_planet_elements(planets, cfg)
    label_elements = create_label_elements(planets, cfg)

    # Assemble scene
    scene = VScene(
        width=cfg["scene"]["width"],
        height=cfg["scene"]["height"],
        background=Color(cfg["scene"]["background"]),
    )
    scene = scene.add_elements(sun_elements)
    scene = scene.add_elements(planet_elements)
    scene = scene.add_elements(label_elements)

    # Export
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
    )


if __name__ == "__main__":
    main()
