"""One-time capability scan for the Skia backend.

The Skia backend renders a scene only if every element and feature in it is
supported; otherwise it stops. check_scene walks the scene once (before any
frame is drawn) and returns a detailed list of what cannot be rendered. The
render loop itself performs no capability checks.

This module knows nothing about SVG/resvg: it only reports. Callers decide
whether to use Skia based on an empty report.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from svan2d.primitive.registry import get_skia_renderer_class_for_state

if TYPE_CHECKING:
    from svan2d.primitive.state.base import State
    from svan2d.vscene.vscene import VScene


def check_scene(scene: "VScene") -> list[str]:
    """Return reasons the scene cannot be rendered by Skia (empty == fully supported)."""
    reasons: list[str] = []
    seen: set[str] = set()

    def add(reason: str) -> None:
        if reason not in seen:
            seen.add(reason)
            reasons.append(reason)

    # Scene-level features.
    if scene.clip_state is not None or scene.mask_state is not None:
        add("scene-level clip/mask")
    if getattr(scene, "_pauses", None):
        add("scene pauses/overlays")
    if getattr(scene, "_camera_offset_func", None) is not None:
        add("animated camera")

    for element in scene.elements:
        _check_element(element, add)

    return reasons


def _check_element(element, add) -> None:
    # VElementGroup: recurse into children; its own state is transform-only.
    if hasattr(element, "elements"):
        group_state = _safe_frame(element)
        if group_state is not None:
            _check_state_features(group_state, add)
        for child in element.elements:
            _check_element(child, add)
        return

    # Element-level clip/mask attachments.
    if getattr(element, "clip_elements", None):
        add("element clip")
    if getattr(element, "mask_element", None) is not None:
        add("element mask")

    # An explicit per-element Skia renderer (e.g. a PathVariantsSkiaRenderer
    # carrying its variant) satisfies the renderer requirement on its own, the
    # way scene.py prefers element._skia_renderer over the registry.
    has_renderer = getattr(element, "_skia_renderer", None) is not None
    for state in _element_states(element):
        _check_state(state, add, has_renderer=has_renderer)


def _check_state(state: "State", add, has_renderer: bool = False) -> None:
    if not has_renderer and get_skia_renderer_class_for_state(state) is None:
        add(f"no Skia renderer for {type(state).__name__}")
    _check_state_features(state, add)
    # StateCollectionState delegates to its children's own renderers, so their
    # features (gradient/clip/missing renderer) must be validated too.
    child_states = getattr(state, "states", None)
    if child_states:
        for child in child_states:
            _check_state(child, add)


def _check_state_features(state: "State", add) -> None:
    if getattr(state, "filter", None) is not None:
        add(f"{type(state).__name__}: filter")
    if state.clip_state is not None or state.clip_states:
        add(f"{type(state).__name__}: clip")
    if state.mask_state is not None or state.mask_states:
        add(f"{type(state).__name__}: mask")
    if getattr(state, "fill_gradient", None) is not None or getattr(state, "stroke_gradient", None) is not None:
        add(f"{type(state).__name__}: gradient")
    # PathBandState carries per-segment gradients (a tuple) rather than a single one.
    stroke_gradients = getattr(state, "stroke_gradients", None)
    if stroke_gradients is not None and any(g is not None for g in stroke_gradients):
        add(f"{type(state).__name__}: gradient")
    if getattr(state, "fill_pattern", None) is not None or getattr(state, "stroke_pattern", None) is not None:
        add(f"{type(state).__name__}: pattern")


def _element_states(element):
    """Yield the declared states of a VElement (frame-independent where possible)."""
    if hasattr(element, "_ensure_built"):
        element._ensure_built()
    keystates = getattr(element, "_keystates_list", None)
    if keystates:
        for ks in keystates:
            yield ks.state
            if getattr(ks, "outgoing_state", None) is not None:
                yield ks.outgoing_state
        return
    # frame_fn elements have no static keystates — sample across the timeline.
    sampled = _safe_frame(element)
    if sampled is not None:
        yield sampled


def _safe_frame(element):
    try:
        return element.get_frame(0.0)
    except Exception:
        return None
