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
from svan2d.skia.clipping import clip_states_of, mask_states_of

if TYPE_CHECKING:
    from svan2d.primitive.state.base import State
    from svan2d.vscene.vscene import VScene


def check_scene(scene) -> list[str]:
    """Return reasons the scene cannot be rendered by Skia (empty == fully supported).

    Takes a VScene, VSceneComposite or VSceneSequence; composites and sequences
    are checked scene by scene, and every transition needs a Skia version.
    """
    reasons: list[str] = []
    seen: set[str] = set()

    def add(reason: str) -> None:
        if reason not in seen:
            seen.add(reason)
            reasons.append(reason)

    _check_any_scene(scene, add)
    return reasons


def _check_any_scene(scene, add) -> None:
    from svan2d.transition.scene.registry import get_skia_transition_class
    from svan2d.vscene.vscene_composite import VSceneComposite
    from svan2d.vscene.vscene_sequence import VSceneSequence, _TransitionEntry

    if isinstance(scene, VSceneComposite):
        for child in scene.scenes:
            _check_any_scene(child, add)
    elif isinstance(scene, VSceneSequence):
        for entry in scene._entries:
            if isinstance(entry, _TransitionEntry):
                if get_skia_transition_class(entry.transition) is None:
                    add(f"no Skia version of transition {type(entry.transition).__name__}")
            else:
                _check_any_scene(entry.scene, add)
    else:
        _check_vscene(scene, add)


def _check_vscene(scene: "VScene", add) -> None:
    # Scene-level features.
    _check_clips_and_masks(
        [scene.clip_state] if scene.clip_state is not None else [],
        [scene.mask_state] if scene.mask_state is not None else [],
        add,
    )
    if getattr(scene, "_pauses", None):
        add("scene pauses/overlays")

    for element in scene.elements:
        _check_element(element, add)


def _check_element(element, add) -> None:
    # VElementGroup: recurse into children; its own state is transform-only.
    if hasattr(element, "elements"):
        group_state = _safe_frame(element)
        if group_state is not None:
            _check_state_features(group_state, add)
        _check_attachments(element, add)
        for child in element.elements:
            _check_element(child, add)
        return

    _check_attachments(element, add)

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
    _check_clips_and_masks(clip_states_of(state), mask_states_of(state), add)
    if getattr(state, "fill_gradient", None) is not None or getattr(state, "stroke_gradient", None) is not None:
        add(f"{type(state).__name__}: gradient")
    # PathBandState carries per-segment gradients (a tuple) rather than a single one.
    stroke_gradients = getattr(state, "stroke_gradients", None)
    if stroke_gradients is not None and any(g is not None for g in stroke_gradients):
        add(f"{type(state).__name__}: gradient")
    if getattr(state, "fill_pattern", None) is not None or getattr(state, "stroke_pattern", None) is not None:
        add(f"{type(state).__name__}: pattern")


def _check_attachments(element, add) -> None:
    """Clips and a mask attached to a VElement or VElementGroup (.clip()/.mask())."""
    for clip_element in getattr(element, "clip_elements", None) or []:
        for state in _element_states(clip_element):
            _check_clips_and_masks([state], [], add)
    mask_element = getattr(element, "mask_element", None)
    if mask_element is not None:
        for state in _element_states(mask_element):
            _check_clips_and_masks([], [state], add)


def _check_clips_and_masks(clips, masks, add) -> None:
    """A clip shape counts only as geometry, so it needs no more than a renderer;
    a mask shape is drawn as it is, so it must be fully supported."""
    for clip in clips:
        if get_skia_renderer_class_for_state(clip) is None:
            add(f"no Skia renderer for {type(clip).__name__} (clip shape)")
    for mask in masks:
        _check_state(mask, add)


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
