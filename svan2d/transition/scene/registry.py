"""Skia versions of scene transitions, assigned as primitives get theirs.

A transition class names its Skia version with a decorator:

    @skia_transition("svan2d.transition.scene.skia.fade:FadeSkia")
    class Fade(SceneTransition):
        ...

The dotted "module:Class" path is resolved on first use, so importing a
transition never imports the optional skia package. Subclasses inherit a base
class's Skia version, and a transition written outside svan2d registers its own
the same way.
"""

from typing import Any, Type

from svan2d.primitive.registry import _resolve_skia

_skia_transition_registry: dict[Type, "str | Type"] = {}
_skia_transition_cache: dict[Type, Any] = {}


def skia_transition(path: str):
    """Decorator placed ON A TRANSITION CLASS to assign its Skia version."""

    def decorator(transition_class: Type) -> Type:
        if transition_class in _skia_transition_registry:
            raise RuntimeError(
                f"Transition '{transition_class.__name__}' already has a Skia version "
                f"({_skia_transition_registry[transition_class]!r})."
            )
        _skia_transition_registry[transition_class] = path
        return transition_class

    return decorator


def get_skia_transition_class(transition: Any) -> Type | None:
    """The Skia version's class for a transition, or None if it has none."""
    for klass in type(transition).__mro__:
        entry = _skia_transition_registry.get(klass)
        if entry is not None:
            resolved = _resolve_skia(entry)
            _skia_transition_registry[klass] = resolved  # cache resolved class
            return resolved
    return None


def get_skia_transition(transition: Any) -> Any:
    """A cached instance of the transition's Skia version, or None."""
    transition_class = get_skia_transition_class(transition)
    if transition_class is None:
        return None
    instance = _skia_transition_cache.get(transition_class)
    if instance is None:
        instance = transition_class()
        _skia_transition_cache[transition_class] = instance
    return instance
