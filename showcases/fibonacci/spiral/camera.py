"""Camera for the Fibonacci Spiral showcase.

PCHIP-interpolated zoom-out with tip-tracking offset.
Scale is derived from cumulative bounding boxes at arc boundaries.
"""

import math
from typing import Callable

from scipy.interpolate import PchipInterpolator

from data_prep import FibonacciData
from svan2d.vscene.vscene import VScene


def build_camera_scale(
    data: FibonacciData,
    scene_w: float,
    scene_h: float,
    padding: float = 1.4,
) -> Callable[[float], float]:
    """Build camera scale using PCHIP interpolation over arc boundary scales.

    Computes the required scale to frame cumulative content at each arc
    boundary, then PCHIP-interpolates for smooth monotone zoom-out.
    """
    bboxes = data.spiral.cumulative_bboxes
    arc_times = data.spiral.arc_times
    scene_min = min(scene_w, scene_h)

    # Sample points: scale needed at each arc boundary
    ts = [arc_times[0][0]]
    scales = []
    b0 = bboxes[0]
    content_0 = max(b0[2] - b0[0], b0[3] - b0[1]) * padding
    scales.append(scene_min / max(content_0, 1))

    n = len(arc_times)
    for i, (_, te) in enumerate(arc_times):
        ts.append(te)
        # Use next arc's bbox so camera is one square ahead
        b = bboxes[min(i + 1, n - 1)]
        extent = max(b[2] - b[0], b[3] - b[1]) * padding
        scales.append(scene_min / max(extent, 1))

    # Hold final scale to t=1.0
    if ts[-1] < 1.0:
        ts.append(1.0)
        scales.append(scales[-1])

    pchip = PchipInterpolator(ts, scales)

    def scale_func(t: float) -> float:
        t = max(ts[0], min(t, ts[-1]))
        return float(pchip(t))

    return scale_func


def apply_camera(
    scene: VScene,
    data: FibonacciData,
    scale_func: Callable[[float], float],
) -> VScene:
    """Apply camera with tip-tracking pan and PCHIP zoom."""
    arcs = data.spiral.arc_geometry
    arc_times = data.spiral.arc_times
    n_arcs = len(arc_times)
    anim_end = arc_times[-1][1]

    fb = data.spiral.cumulative_bboxes[-1]
    final_center = ((fb[0] + fb[2]) / 2, (fb[1] + fb[3]) / 2)
    last_tip = arcs[-1]["end"]

    # Precompute SVG-matching arc centers and sweeps.
    # The SVG path uses 'A r,r 0 0 0' (sweep-flag=0, large-arc=0).
    # arc_params centers don't always match the SVG arc center, so
    # we derive the correct center from start/end points.
    svg_arcs = []
    for geo in arcs:
        sx, sy = geo["start"]
        ex, ey = geo["end"]
        r = geo["arc_params"][2]
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        dx, dy = ex - sx, ey - sy
        chord = math.sqrt(dx * dx + dy * dy)
        h = math.sqrt(max(r * r - (chord / 2) ** 2, 0))
        # Perpendicular (CW rotation) gives the sweep-flag=0 center
        px, py = dy / chord, -dx / chord
        cx, cy = mx + h * px, my + h * py
        sa = math.atan2(sy - cy, sx - cx)
        ea = math.atan2(ey - cy, ex - cx)
        sw = ea - sa
        if sw > 0:
            sw -= 2 * math.pi
        svg_arcs.append((cx, cy, r, sa, sw))

    def offset_func(t: float) -> tuple[float, float]:
        if t <= arc_times[0][0]:
            return arcs[0]["start"]
        if t >= anim_end:
            ht = min((t - anim_end) / (1.0 - anim_end), 1.0) if anim_end < 1.0 else 1.0
            return (
                last_tip[0] + (final_center[0] - last_tip[0]) * ht,
                last_tip[1] + (final_center[1] - last_tip[1]) * ht,
            )
        for i in range(n_arcs):
            ts, te = arc_times[i]
            if t <= te:
                lt = (t - ts) / (te - ts) if te > ts else 1.0
                cx, cy, r, sa, sw = svg_arcs[i]
                angle = sa + lt * sw
                return (cx + r * math.cos(angle), cy + r * math.sin(angle))
        return last_tip

    return scene.animate_camera(offset=offset_func, scale=scale_func)
