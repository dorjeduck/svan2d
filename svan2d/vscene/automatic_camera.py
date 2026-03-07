"""Auto-camera: automatically compute camera zoom/pan to frame all content.

Given a fully defined animation, samples scene bounds over time and builds
smooth PCHIP-interpolated camera functions to keep all content framed.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from svan2d.core.point2d import Point2D
from svan2d.vscene.bounds import scene_bounds_at

if TYPE_CHECKING:
    from svan2d.vscene.vscene import OffsetFunc, ScaleFunc, VScene
else:
    OffsetFunc = None


def _clamp_to_active(t: float, freeze: list[tuple[float, float]]) -> float:
    """If t falls inside a freeze interval, clamp it to the interval start."""
    for start, end in freeze:
        if start <= t <= end:
            return start
    return t


def compute_automatic_camera(
    scene: "VScene",
    padding: float = 1.2,
    samples: int | None = None,
    offset: "Point2D | OffsetFunc | None" = None,
    exclude: list | None = None,
    freeze: list[tuple[float, float]] | None = None,
    sample_times: list[float] | None = None,
) -> "tuple[ScaleFunc, OffsetFunc]":
    """Compute camera scale and offset functions from scene bounds.

    Returns the functions without applying them, useful when other elements
    need access to the camera functions before the camera is applied.

    Args:
        scene: A fully defined VScene with elements and keystates.
        padding: Scale padding factor (1.2 = 20% margin around content).
        samples: Number of evenly-spaced time samples for PCHIP interpolation.
                 Defaults to 50. Mutually exclusive with sample_times.
        offset: Optional camera offset. Can be a Point2D (constant offset),
                a callable (t -> Point2D), or None (auto-compute from content center).
        exclude: Elements to skip when computing bounds.
        freeze: List of (start, end) time intervals where the camera
                holds steady. During a freeze interval, bounds are sampled
                at the interval start time.
        sample_times: Explicit list of times (0–1) at which to sample bounds.
                      Mutually exclusive with samples.

    Returns:
        (scale_func, offset_func) tuple.
    """
    if sample_times is not None and samples is not None:
        raise ValueError(
            "sample_times and samples are mutually exclusive — provide one, not both."
        )

    try:
        from scipy.interpolate import PchipInterpolator
    except ImportError:
        raise RuntimeError(
            "automatic_camera requires scipy. Install it with: pip install scipy"
        )

    if sample_times is not None:
        ts = sorted(set(sample_times))
    else:
        n = samples if samples is not None else 50
        ts = [i / (n - 1) for i in range(n)]

    # Normalize offset: Point2D → constant function
    if isinstance(offset, Point2D):
        _pt = offset
        offset_func: OffsetFunc | None = lambda t, _p=_pt: _p
    elif offset is not None:
        offset_func = offset
    else:
        offset_func = None

    scales = []
    offsets_x = []
    offsets_y = []
    auto_offset = offset_func is None

    scene_w = scene.width
    scene_h = scene.height

    for t in ts:
        sample_t = _clamp_to_active(t, freeze) if freeze else t
        bounds = scene_bounds_at(scene, sample_t, exclude=exclude)

        if bounds is None:
            scales.append(1.0)
            offsets_x.append(0.0)
            offsets_y.append(0.0)
            continue

        bmin_x, bmin_y, bmax_x, bmax_y = bounds

        if auto_offset:
            cx = (bmin_x + bmax_x) / 2
            cy = (bmin_y + bmax_y) / 2
            offsets_x.append(cx)
            offsets_y.append(cy)
            extent_x = bmax_x - bmin_x
            extent_y = bmax_y - bmin_y
        else:
            pt = offset_func(t)
            offsets_x.append(pt.x)
            offsets_y.append(pt.y)
            extent_x = 2 * max(abs(bmax_x - pt.x), abs(bmin_x - pt.x))
            extent_y = 2 * max(abs(bmax_y - pt.y), abs(bmin_y - pt.y))

        if extent_x <= 0 or extent_y <= 0:
            scales.append(1.0)
        else:
            scale_val = min(scene_w / extent_x, scene_h / extent_y) / padding
            scales.append(scale_val)

    # Build PCHIP interpolators — clamp to sample range to hold first/last
    # value for times outside the sampled interval.
    t_lo, t_hi = ts[0], ts[-1]
    scale_interp = PchipInterpolator(ts, scales)
    scale_func: ScaleFunc = lambda t, _interp=scale_interp, _lo=t_lo, _hi=t_hi: float(
        _interp(max(_lo, min(_hi, t)))
    )

    if auto_offset:
        ox_interp = PchipInterpolator(ts, offsets_x)
        oy_interp = PchipInterpolator(ts, offsets_y)
        result_offset: OffsetFunc = (
            lambda t, _ox=ox_interp, _oy=oy_interp, _lo=t_lo, _hi=t_hi: Point2D(
                float(_ox(max(_lo, min(_hi, t)))),
                float(_oy(max(_lo, min(_hi, t)))),
            )
        )
    else:
        result_offset = offset_func  # type: ignore[assignment]

    return scale_func, result_offset


def automatic_camera(
    scene: "VScene",
    padding: float = 1.2,
    samples: int | None = None,
    offset: "Point2D | OffsetFunc | None" = None,
    pivot: "Point2D | None" = None,
    easing: Callable[[float], float] | None = None,
    exclude: list | None = None,
    freeze: list[tuple[float, float]] | None = None,
    sample_times: list[float] | None = None,
) -> "VScene":
    """Automatically compute camera zoom/pan so all content stays framed.

    Args:
        scene: A fully defined VScene with elements and keystates.
        padding: Scale padding factor (1.2 = 20% margin around content).
        samples: Number of evenly-spaced time samples for PCHIP interpolation.
                 Defaults to 50. Mutually exclusive with sample_times.
        offset: Optional camera offset. Can be a Point2D (constant offset),
                a callable (t -> Point2D), or None (auto-compute from content center).
        pivot: Camera pivot point (Point2D). Passed to animate_camera.
        easing: Easing function. Passed to animate_camera.
        exclude: Elements to skip when computing bounds.
        freeze: List of (start, end) time intervals where the camera
                holds steady.
        sample_times: Explicit list of times (0–1) at which to sample bounds.
                      Mutually exclusive with samples.

    Returns:
        New VScene with camera animation configured.
    """
    result_scale, result_offset = compute_automatic_camera(
        scene, padding, samples, offset, exclude, freeze, sample_times
    )

    return scene.animate_camera(
        scale=result_scale,
        offset=result_offset,
        pivot=pivot,
        easing=easing,
    )
