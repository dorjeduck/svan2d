import math
import random

from svan2d.core.point2d import Point2D
from svan2d.transition import curve, easing
from svan2d.transition.easing import easing2D


def scatter_entrance(
    target: Point2D,
    radius: float,
    max_rotation: float,
    rng: random.Random,
    radius_inner_factor: float = 0.6,
    perp_scale_range: float = 0.4,
) -> tuple[Point2D, float, dict, dict]:
    """Compute scatter entrance parameters for a character flying in along a bezier arc.

    Returns (origin, rotation, easing_dict, interpolation_dict). The caller builds
    the hidden state via replace(visible, pos=origin, scale=0.0, opacity=0.0, rotation=rotation).

    Args:
        target: Final resting position of the element.
        radius: Maximum scatter distance from target.
        max_rotation: Maximum initial rotation in degrees (±).
        rng: Random number generator.
        radius_inner_factor: Minimum distance as a fraction of radius (default 0.6).
        perp_scale_range: Maximum perpendicular deflection of the bezier control point (default 0.4).

    Returns:
        (origin, rotation, easing_dict, interpolation_dict)
    """
    angle = rng.uniform(0, 2 * math.pi)
    dist = rng.uniform(radius * radius_inner_factor, radius)
    origin = Point2D(
        target.x + math.cos(angle) * dist,
        target.y + math.sin(angle) * dist,
    )
    rot = rng.uniform(-max_rotation, max_rotation)

    mid = Point2D((origin.x + target.x) / 2, (origin.y + target.y) / 2)
    dx, dy = target.x - origin.x, target.y - origin.y
    perp_scale = rng.uniform(-perp_scale_range, perp_scale_range)
    cp = Point2D(mid.x + (-dy) * perp_scale, mid.y + dx * perp_scale)

    entrance_easing = {
        "pos": easing2D(easing.out_cubic, easing.out_back),
        "scale": easing.out_back,
        "opacity": easing.out_cubic,
        "rotation": easing.out_cubic,
    }
    entrance_curve = {"pos": curve.bezier([cp])}

    return origin, rot, entrance_easing, entrance_curve
