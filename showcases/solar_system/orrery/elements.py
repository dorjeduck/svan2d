"""VElement builders for the solar system orrery."""

import math

from planets import PlanetData, EARTH_PERIOD, elliptical_orbital_curve

from svan2d.component.state.circle import CircleState
from svan2d.component.state.ellipse import EllipseState
from svan2d.component.state.text import TextState
from svan2d.core.color import Color
from svan2d.core.point2d import Point2D
from svan2d.velement.velement import VElement


def create_sun_element(
    sun_px: float, glow_px: float, cfg: dict
) -> list[VElement]:
    """Create sun circle (and optional glow) at the scene center."""
    sun_cfg = cfg["sun"]
    center = Point2D(0, 0)

    elements: list[VElement] = []

    # Glow behind sun
    glow_state = CircleState(
        radius=glow_px,
        pos=center,
        fill_color=Color(sun_cfg["color"]),
        fill_opacity=sun_cfg["glow_opacity"],
        stroke_width=0,
    )
    elements.append(VElement(state=glow_state))

    # Sun body
    sun_state = CircleState(
        radius=sun_px,
        pos=center,
        fill_color=Color(sun_cfg["color"]),
        stroke_width=0,
    )
    elements.append(VElement(state=sun_state))

    return elements


def create_orbit_ring_elements(
    planets: list[PlanetData],
    orbit_radii: dict[str, float],
    cfg: dict,
) -> list[VElement]:
    """Create orbit ring ellipses (no fill, just stroke)."""
    ring_cfg = cfg["orbits"]["ring"]

    elements: list[VElement] = []
    for p in planets:
        a = orbit_radii[p.name]
        e = p.eccentricity
        b = a * math.sqrt(1 - e * e)
        c = a * e  # focal offset
        # Sun is at scene center; ellipse geometric center is offset upward
        # (In the rotated frame, the focus-to-center vector points to -y)
        ellipse_center = Point2D(0, -c)
        state = EllipseState(
            rx=b,   # after 90° rotation: original b becomes horizontal
            ry=a,   # original a becomes vertical
            pos=ellipse_center,
            fill_opacity=0.0,
            stroke_color=Color(ring_cfg["stroke_color"]),
            stroke_width=ring_cfg["stroke_width"],
            stroke_opacity=ring_cfg["stroke_opacity"],
        )
        elements.append(VElement(state=state))
    return elements


def create_planet_elements(
    planets: list[PlanetData],
    orbit_radii: dict[str, float],
    body_radii: dict[str, float],
    cfg: dict,
) -> list[VElement]:
    """Create animated planet elements with orbital interpolation."""
    center = Point2D(0, 0)
    earth_orbits = cfg["animation"]["earth_orbits"]

    elements: list[VElement] = []
    for p in planets:
        radius_px = body_radii[p.name]
        revolutions = (EARTH_PERIOD / p.orbital_period_days) * earth_orbits

        a = orbit_radii[p.name]
        e = p.eccentricity
        c = a * e
        # Aphelion at top: after 90° CCW rotation, aphelion is at y = -(a + c)
        start_pos = Point2D(center.x, center.y - (a + c))

        state = CircleState(
            radius=radius_px,
            pos=start_pos,
            fill_color=Color(p.color),
            stroke_width=0,
        )

        element = (
            VElement()
            .keystate(state, at=0.0)
            .transition(
                interpolation_dict={
                    "pos": elliptical_orbital_curve(
                        a, e, center, revolutions
                    )
                }
            )
            .keystate(state, at=1.0)
        )
        elements.append(element)
    return elements


def create_label_elements(
    planets: list[PlanetData],
    orbit_radii: dict[str, float],
    body_radii: dict[str, float],
    cfg: dict,
) -> list[VElement]:
    """Create text labels that follow their planets."""
    label_cfg = cfg["planets"]["labels"]
    if not label_cfg["show"]:
        return []

    center = Point2D(0, 0)
    earth_orbits = cfg["animation"]["earth_orbits"]
    offset_y = label_cfg["offset_y"]

    elements: list[VElement] = []
    for p in planets:
        revolutions = (EARTH_PERIOD / p.orbital_period_days) * earth_orbits
        planet_radius_px = body_radii[p.name]

        a = orbit_radii[p.name]
        e = p.eccentricity
        c = a * e
        label_y_offset = offset_y - planet_radius_px

        # Label start: above planet's aphelion position
        start_pos = Point2D(center.x, center.y - (a + c) + label_y_offset)

        # Label orbit center: same focal offset as planet, plus label shift
        label_center = Point2D(center.x, center.y + label_y_offset)

        state = TextState(
            text=p.name,
            pos=start_pos,
            font_family=label_cfg["font_family"],
            font_size=label_cfg["font_size"],
            fill_color=Color(label_cfg["font_color"]),
            text_anchor="middle",
            dominant_baseline="auto",
            stroke_width=0,
        )

        element = (
            VElement()
            .keystate(state, at=0.0)
            .transition(
                interpolation_dict={
                    "pos": elliptical_orbital_curve(
                        a, e, label_center, revolutions
                    )
                }
            )
            .keystate(state, at=1.0)
        )
        elements.append(element)
    return elements
