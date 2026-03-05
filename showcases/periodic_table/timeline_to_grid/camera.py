"""Camera for the Timeline-to-Grid showcase.

PCHIP-interpolated zoom-out that tracks the buildup frontier.
Scale is derived from the bounding box of visible cells at each
element appearance time. The scale_func is also passed to elements
(e.g., year label) so they can compensate for zoom.
"""

from typing import Callable

from scipy.interpolate import PchipInterpolator

from data_prep import AppData
from svan2d.vscene.vscene import VScene


def build_camera_scale(
    data: AppData,
    scene_w: float,
    scene_h: float,
    padding: float = 1.15,
) -> Callable[[float], float]:
    """Build camera scale using PCHIP interpolation over element appearance times.

    At each appearance, computes the scale needed to frame all visible cells.
    PCHIP gives smooth monotone interpolation between sample points.
    """
    cells = data.cells
    n = len(cells)
    axis_x_start = data.axis_x_start
    axis_span = data.axis_x_end - axis_x_start
    spacing = axis_span / max(n - 1, 1)
    tl_cell = data.tl_cell_size

    buildup_end = cells[-1].t_appear_end
    ts: list[float] = []
    scales: list[float] = []

    for i, cell in enumerate(cells):
        t = cell.t_appear
        if ts and t <= ts[-1]:
            continue

        frontier_x = axis_x_start + i * spacing
        content_w = (frontier_x - axis_x_start + tl_cell) * padding
        scale = max(scene_w / max(content_w, tl_cell), 1.0)

        ts.append(t)
        scales.append(scale)

    # Hold at 1.0 from buildup_end through end
    if ts[-1] < buildup_end:
        ts.append(buildup_end)
        scales.append(1.0)
    if ts[-1] < 1.0:
        ts.append(1.0)
        scales.append(1.0)

    pchip = PchipInterpolator(ts, scales)

    def scale_func(t: float) -> float:
        t = max(ts[0], min(t, ts[-1]))
        return float(max(pchip(t), 1.0))

    return scale_func


def build_camera_offset(
    data: AppData,
) -> Callable[[float], tuple[float, float]]:
    """Build camera offset using PCHIP interpolation.

    Tracks the center of visible cells horizontally, centered on cell
    row vertically. Eases to origin by buildup_end.
    """
    cells = data.cells
    n = len(cells)
    axis_x_start = data.axis_x_start
    axis_span = data.axis_x_end - axis_x_start
    spacing = axis_span / max(n - 1, 1)
    tl_cell = data.tl_cell_size
    tl_y = data.axis_y - tl_cell / 2 - data.tl_cell_gap

    ts: list[float] = []
    offsets_x: list[float] = []

    for i, cell in enumerate(cells):
        t = cell.t_appear
        if ts and t <= ts[-1]:
            continue

        frontier_x = axis_x_start + i * spacing
        center_x = (axis_x_start + frontier_x) / 2

        ts.append(t)
        offsets_x.append(center_x)

    # Ease to origin at buildup_end
    buildup_end = cells[-1].t_appear_end
    if ts[-1] < buildup_end:
        ts.append(buildup_end)
        offsets_x.append(0.0)
    if ts[-1] < 1.0:
        ts.append(1.0)
        offsets_x.append(0.0)

    ox_pchip = PchipInterpolator(ts, offsets_x)

    def offset_func(t: float) -> tuple[float, float]:
        t = max(ts[0], min(t, ts[-1]))
        return (float(ox_pchip(t)), tl_y)

    return offset_func


def apply_camera(
    scene: VScene,
    scale_func: Callable[[float], float],
    offset_func: Callable[[float], tuple[float, float]],
) -> VScene:
    """Apply PCHIP camera to the scene."""
    return scene.animate_camera(scale=scale_func, offset=offset_func)
