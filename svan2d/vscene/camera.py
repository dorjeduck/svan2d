"""Camera interpolation and transform functions for VScene."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from svan2d.core.point2d import Point2D
from svan2d.vscene.camera_state import CameraState

if TYPE_CHECKING:
    from svan2d.vscene.vscene import EasingFunc, OffsetFunc, RotationFunc, ScaleFunc


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _eased_t(
    easing_dict: dict | None,
    field: str,
    local_t: float,
    linear: Callable[[float], float],
) -> float:
    fn = easing_dict.get(field, linear) if easing_dict else linear
    return fn(local_t)


def has_camera_funcs(
    scale_func: ScaleFunc | None,
    offset_func: OffsetFunc | None,
    rotation_func: RotationFunc | None,
) -> bool:
    return scale_func is not None or offset_func is not None or rotation_func is not None


def get_camera_state_at_time(
    frame_time: float,
    camera_keystates: list[tuple[CameraState, float, dict | None]],
    camera_scale_func: ScaleFunc | None,
    camera_offset_func: OffsetFunc | None,
    camera_rotation_func: RotationFunc | None,
    camera_func_easing: EasingFunc | None,
    scene_scale: float,
    scene_rotation: float,
    scene_offset_x: float,
    scene_offset_y: float,
) -> CameraState:
    """Get interpolated camera state with visually linear panning.

    Uses custom interpolation that compensates pos for scale changes,
    ensuring camera movement appears linear on screen regardless of zoom.
    """
    from svan2d.transition import easing as easing_module

    if len(camera_keystates) < 2:
        if len(camera_keystates) == 1:
            state = camera_keystates[0][0]
        else:
            # No camera animation - return static properties
            state = CameraState(
                scale=scene_scale,
                rotation=scene_rotation,
                pos=Point2D(scene_offset_x, scene_offset_y),
            )

        if has_camera_funcs(camera_scale_func, camera_offset_func, camera_rotation_func):
            return apply_camera_functions(
                state, frame_time,
                camera_scale_func, camera_offset_func,
                camera_rotation_func, camera_func_easing,
            )
        return state

    keystates = camera_keystates

    # Handle boundary cases
    boundary_state = None
    if frame_time <= keystates[0][1]:
        boundary_state = keystates[0][0]
    elif frame_time >= keystates[-1][1]:
        boundary_state = keystates[-1][0]

    if boundary_state is not None:
        if has_camera_funcs(camera_scale_func, camera_offset_func, camera_rotation_func):
            return apply_camera_functions(
                boundary_state, frame_time,
                camera_scale_func, camera_offset_func,
                camera_rotation_func, camera_func_easing,
            )
        return boundary_state

    # Find segment
    start_state, start_time, easing_dict = keystates[0]
    end_state, end_time, _ = keystates[1]

    for i in range(len(keystates) - 1):
        if keystates[i][1] <= frame_time <= keystates[i + 1][1]:
            start_state, start_time, easing_dict = keystates[i]
            end_state, end_time, _ = keystates[i + 1]
            break

    # Compute local t (0-1 within segment)
    if end_time == start_time:
        local_t = 0.0
    else:
        local_t = (frame_time - start_time) / (end_time - start_time)

    # Apply easing
    linear = easing_module.linear
    scale_t = _eased_t(easing_dict, "scale", local_t, linear)
    pos_t = _eased_t(easing_dict, "pos", local_t, linear)
    rotation_t = _eased_t(easing_dict, "rotation", local_t, linear)

    # CameraState fields are guaranteed non-None after __post_init__
    assert start_state.scale is not None and end_state.scale is not None
    assert start_state.rotation is not None and end_state.rotation is not None
    assert start_state.pos is not None and end_state.pos is not None
    assert start_state.pivot is not None and end_state.pivot is not None
    assert start_state.opacity is not None and end_state.opacity is not None

    # Interpolate scale and rotation normally
    interp_scale = _lerp(start_state.scale, end_state.scale, scale_t)
    interp_rotation = _lerp(start_state.rotation, end_state.rotation, rotation_t)

    # For visually linear panning: interpolate "visual target" (pos * scale)
    # then derive world pos from that
    start_visual = Point2D(
        start_state.pos.x * start_state.scale, start_state.pos.y * start_state.scale
    )
    end_visual = Point2D(
        end_state.pos.x * end_state.scale, end_state.pos.y * end_state.scale
    )

    # Interpolate visual target linearly (using pos easing)
    interp_visual = Point2D(
        _lerp(start_visual.x, end_visual.x, pos_t),
        _lerp(start_visual.y, end_visual.y, pos_t),
    )

    # Convert back to world pos
    if interp_scale != 0:
        interp_pos = Point2D(
            interp_visual.x / interp_scale, interp_visual.y / interp_scale
        )
    else:
        interp_pos = Point2D(0, 0)

    # Interpolate pivot (simple linear)
    interp_pivot = Point2D(
        _lerp(start_state.pivot.x, end_state.pivot.x, local_t),
        _lerp(start_state.pivot.y, end_state.pivot.y, local_t),
    )

    # Interpolate opacity
    interp_opacity = _lerp(start_state.opacity, end_state.opacity, local_t)

    result = CameraState(
        scale=interp_scale,
        rotation=interp_rotation,
        pos=interp_pos,
        pivot=interp_pivot,
        opacity=interp_opacity,
    )
    if has_camera_funcs(camera_scale_func, camera_offset_func, camera_rotation_func):
        return apply_camera_functions(
            result, frame_time,
            camera_scale_func, camera_offset_func,
            camera_rotation_func, camera_func_easing,
        )
    return result


def apply_camera_functions(
    base_state: CameraState,
    frame_time: float,
    scale_func: ScaleFunc | None,
    offset_func: OffsetFunc | None,
    rotation_func: RotationFunc | None,
    func_easing: EasingFunc | None,
) -> CameraState:
    """Apply camera functions to a base state at given frame_time."""
    from svan2d.transition import easing as easing_module

    easing_fn = func_easing or easing_module.linear
    eased_frame_time = easing_fn(frame_time)

    scale = base_state.scale
    rotation = base_state.rotation
    pos = base_state.pos

    if scale_func is not None:
        scale = scale_func(eased_frame_time)

    if rotation_func is not None:
        rotation = rotation_func(eased_frame_time)

    if offset_func is not None:
        pos = offset_func(eased_frame_time)

    return CameraState(
        scale=scale,
        rotation=rotation,
        pos=pos,
        pivot=base_state.pivot,
        opacity=base_state.opacity,
    )


def build_camera_transform(
    state: CameraState,
    render_scale: float,
    viewport_width: float = 0.0,
    viewport_height: float = 0.0,
) -> str:
    """Build SVG transform string from camera state with pivot support.

    viewport_width / viewport_height must be supplied (in rendered pixels) when
    the scene uses a non-center origin so the camera centers on the offset point
    rather than placing it at the viewport's top-left corner.
    """
    assert (
        state.scale is not None
        and state.pivot is not None
        and state.rotation is not None
    )

    parts = []
    total_scale = state.scale * render_scale

    has_pivot = state.pivot.x != 0 or state.pivot.y != 0
    has_transform = total_scale != 1.0 or state.rotation != 0

    # Pivot: translate to pivot point (negate Y: user Cartesian → SVG Y-down)
    if has_pivot and has_transform:
        parts.append(f"translate({state.pivot.x},{-state.pivot.y})")

    if total_scale != 1.0:
        parts.append(f"scale({total_scale})")

    if state.rotation != 0:
        parts.append(f"rotate({-state.rotation})")  # Negate: user CCW → SVG CW

    if has_pivot and has_transform:
        parts.append(f"translate({-state.pivot.x},{state.pivot.y})")

    # Camera position LAST (world space - applied first in SVG right-to-left order)
    if state.x != 0 or state.y != 0:
        parts.append(f"translate({-state.x},{state.y})")  # Negate Y: user Cartesian → SVG Y-down

    # Non-center origins: shift the target from SVG (0,0) to the viewport center.
    # Prepend so it is the outermost transform (applied last in SVG right-to-left order).
    if viewport_width or viewport_height:
        parts.insert(0, f"translate({viewport_width / 2},{viewport_height / 2})")

    return " ".join(parts)
