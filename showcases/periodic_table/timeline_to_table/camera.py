"""Camera for the Timeline-to-Grid showcase.

Uses automatic_camera to derive scale/offset from scene bounds.
compute_automatic_camera returns the functions before applying them,
so year_element can use them for font-size compensation.
"""

from collections.abc import Callable

from svan2d.core.point2d import Point2D
from svan2d.vscene.automatic_camera import compute_automatic_camera
from svan2d.vscene.vscene import VScene


def build_camera_funcs(
    scene: VScene,
    padding: float = 1.15,
    samples: int | None = 100,
    exclude: list | None = None,
    freeze: list[tuple[float, float]] | None = None,
    sample_times: list[float] | None = None,
) -> tuple[Callable[[float], float], Callable[[float], Point2D]]:
    """Compute auto-camera scale and offset from scene bounds.

    Returns (scale_func, offset_func) without applying them to the scene.
    """
    return compute_automatic_camera(
        scene,
        padding=padding,
        samples=samples if sample_times is None else None,
        exclude=exclude,
        freeze=freeze,
        sample_times=sample_times,
    )


def apply_camera(
    scene: VScene,
    scale_func: Callable[[float], float],
    offset_func: Callable[[float], Point2D],
) -> VScene:
    """Apply pre-computed camera functions to the scene."""
    return scene.animate_camera(scale=scale_func, offset=offset_func)
