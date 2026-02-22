"""Planet data constants and orbital math utilities."""

import math
from dataclasses import dataclass

from svan2d.core.point2d import Point2D


@dataclass
class PlanetData:
    name: str
    orbital_radius_au: float  # astronomical units
    orbital_period_days: float  # Earth days for one orbit
    radius_km: float  # actual radius
    color: str  # default hex color
    eccentricity: float = 0.0  # orbital eccentricity (0 = circle, <1 = ellipse)


PLANETS = {
    "Mercury": PlanetData("Mercury", 0.39, 87.97, 2439.7, "#b0b0b0", 0.2056),
    "Venus": PlanetData("Venus", 0.72, 224.7, 6051.8, "#e8cda0", 0.0068),
    "Earth": PlanetData("Earth", 1.00, 365.25, 6371.0, "#4a90d9", 0.0167),
    "Mars": PlanetData("Mars", 1.52, 687.0, 3389.5, "#c1440e", 0.0934),
    "Jupiter": PlanetData("Jupiter", 5.20, 4332.6, 69911.0, "#c88b3a", 0.0484),
    "Saturn": PlanetData("Saturn", 9.58, 10759.2, 58232.0, "#e8d5a3", 0.0539),
    "Uranus": PlanetData("Uranus", 19.2, 30688.5, 25362.0, "#7ec8e3", 0.0473),
    "Neptune": PlanetData("Neptune", 30.1, 60182.0, 24622.0, "#3f54ba", 0.0086),
}

EARTH_PERIOD = PLANETS["Earth"].orbital_period_days
SUN_RADIUS_KM = 696_340.0


def get_planets(names: list[str]) -> list[PlanetData]:
    """Filter PLANETS by a list of names."""
    return [PLANETS[name] for name in names if name in PLANETS]


def orbital_curve(
    radius_px: float, center: Point2D, revolutions: float
):
    """Return an interpolation function for circular orbit.

    The returned function ignores p1/p2 and computes position from t directly,
    following the same pattern as DFT epicycles.
    """

    def curve(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        angle = 2 * math.pi * t * revolutions
        return Point2D(
            center.x + radius_px * math.sin(angle),
            center.y - radius_px * math.cos(angle),  # SVG y-flip: up = negative
        )

    return curve


def _solve_kepler(M: float, e: float, iterations: int = 6) -> float:
    """Solve M = E - e*sin(E) for eccentric anomaly E via Newton's method."""
    E = M
    for _ in range(iterations):
        E -= (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    return E


def elliptical_orbital_curve(
    semi_major_px: float,
    eccentricity: float,
    center: Point2D,
    revolutions: float,
):
    """Return an interpolation function for an elliptical orbit.

    The Sun sits at one focus of the ellipse (at `center`).
    Kepler's equation gives physically accurate non-uniform speed.
    The orbit is rotated so the planet starts at the top (aphelion at 12 o'clock).
    """
    a = semi_major_px
    e = eccentricity
    b = a * math.sqrt(1 - e * e)
    c = a * e  # focal distance

    def curve(p1: Point2D, p2: Point2D, t: float) -> Point2D:
        # Offset by π so t=0 starts at aphelion (E=π → top of orbit)
        M = math.pi + 2 * math.pi * t * revolutions
        E = _solve_kepler(M, e)
        # Standard ellipse with center at geometric center:
        #   x_ell = a*cos(E), y_ell = b*sin(E)
        # Shift so the focus (Sun) is at origin: x_focus = a*cos(E) - c
        x_focus = a * math.cos(E) - c
        y_focus = b * math.sin(E)
        # Rotate 90° CCW so aphelion (E=π → x_focus = -(a+c)) goes to top.
        # Rotation by +90°: x' = -y, y' = x
        # In SVG coords (y-down), "top" means negative y, so: x' = -y_focus, y' = -x_focus
        return Point2D(
            center.x - y_focus,
            center.y + x_focus,  # + because SVG y-down; aphelion gives negative x_focus → top
        )

    return curve
