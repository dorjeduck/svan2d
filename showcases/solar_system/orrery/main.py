"""Solar System Orrery — animated planets orbiting the sun."""

import sys
import tomllib
from pathlib import Path

# Add shared/ and local directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from planets import get_planets, SUN_RADIUS_KM
from scaling import scale_values

from elements import (
    create_sun_element,
    create_orbit_ring_elements,
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

    padding = cfg["scene"]["padding"]
    max_body_px = cfg["bodies"]["max_radius_px"]

    # Reserve space for label above outermost planet at aphelion
    label_cfg = cfg["planets"]["labels"]
    label_margin = (
        abs(label_cfg["offset_y"]) + label_cfg["font_size"] if label_cfg["show"] else 0
    )
    outermost = max(planets, key=lambda p: p.orbital_radius_au)
    # available_px is the semi-major axis of the outermost orbit;
    # aphelion reach is a*(1+e), plus label_margin, plus padding must fit in half the scene
    available_px = (cfg["scene"]["height"] / 2 - padding - label_margin) / (
        1 + outermost.eccentricity
    )

    # Compute orbit radii — outermost orbit fills available space
    orbit_radii = scale_values(
        {p.name: p.orbital_radius_au for p in planets},
        cfg["orbits"]["scaling"],
        available_px,
    )

    # Compute body radii — Sun + planets, largest (Sun) gets max_body_px
    body_values = {"Sun": SUN_RADIUS_KM}
    body_values.update({p.name: p.radius_km for p in planets})
    body_radii = scale_values(body_values, cfg["bodies"]["scaling"], max_body_px)

    sun_px = body_radii["Sun"]
    glow_px = sun_px * 1.4

    # Build elements
    sun_elements = create_sun_element(sun_px, glow_px, cfg)
    ring_elements = create_orbit_ring_elements(planets, orbit_radii, cfg)
    planet_elements = create_planet_elements(planets, orbit_radii, body_radii, cfg)
    label_elements = create_label_elements(planets, orbit_radii, body_radii, cfg)

    # Assemble scene
    scene = VScene(
        width=cfg["scene"]["width"],
        height=cfg["scene"]["height"],
        background=Color(cfg["scene"]["background"]),
    )
    scene = scene.add_elements(sun_elements)
    scene = scene.add_elements(ring_elements)
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
