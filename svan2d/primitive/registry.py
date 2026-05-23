"""
Renderer registry for automatic state→renderer mapping.

This module provides a registry system that associates state classes with
their renderer classes via a decorator placed on the *state class*.

Usage:
    In renderer file:
        class CircleRenderer(Renderer):
            ...

    In state file:
        @renderer(CircleRenderer)
        class CircleState(VertexState):
            ...

    Subclasses can override manually if desired:
        class FancyCircleState(CircleState):
            def get_renderer_class(self):
                return FancyCircleRenderer
"""

import importlib
from typing import Any, Type

# Maps state classes → renderer classes
_renderer_registry: dict[Type, Type] = {}

# Singleton cache for stateless renderer instances
_renderer_cache: dict[Type, Any] = {}


def renderer(renderer_class):
    """
    Decorator used ON A STATE CLASS to assign its renderer.

    Args:
        renderer_class: Either a renderer class or a callable that returns one (for lazy loading)

    Example:
        @renderer(CircleRenderer)
        class CircleState(VertexState):
            ...

        Or with lazy loading (to avoid circular imports):
        @renderer(lambda: CircleRenderer)
        class CircleState(VertexState):
            ...
    """
    def decorator(state_class: Type):
        # Prevent accidentally assigning multiple renderers to one state
        if state_class in _renderer_registry:
            raise RuntimeError(
                f"State '{state_class.__name__}' is already registered with a renderer. "
                f"Cannot register multiple renderers for the same state."
            )

        # Store the original (possibly callable) renderer_class
        # Do NOT resolve it here - that would trigger imports during decoration
        _renderer_registry[state_class] = renderer_class
        return state_class

    return decorator


def get_renderer_class_for_state(state: Any) -> Type | None:
    """Resolve the renderer class for the given state instance.

    State subclasses may override ``get_renderer_class()`` to bypass the registry.
    """
    cls = state.__class__

    # Manual override takes precedence
    if hasattr(state, "get_renderer_class"):
        custom = state.get_renderer_class()
        if custom is not None:
            return custom

    renderer_class_or_callable = _renderer_registry.get(cls)

    # If it's a callable (lazy loader), resolve it now and cache
    if callable(renderer_class_or_callable) and not isinstance(renderer_class_or_callable, type):
        renderer_class = renderer_class_or_callable()
        # Cache the resolved class for next time
        _renderer_registry[cls] = renderer_class
        return renderer_class

    return renderer_class_or_callable


def get_renderer_instance_for_state(state: Any) -> Any:
    """
    Retrieve the cached renderer instance for a state.
    Instantiates and caches the renderer automatically.
    """
    renderer_class = get_renderer_class_for_state(state)
    if renderer_class is None:
        raise RuntimeError(
            f"No renderer registered for state type: {state.__class__.__name__}. "
            f"Add @renderer(RendererClass) decorator to the state class definition."
        )

    # Cache renderer instances by their class
    if renderer_class not in _renderer_cache:
        _renderer_cache[renderer_class] = renderer_class()

    return _renderer_cache[renderer_class]


def is_renderer_registered_for_state(state_class: Type) -> bool:
    """Check whether a state class has a renderer registered."""
    return state_class in _renderer_registry


def get_all_registered_state_renderer_pairs():
    """Return list of (state_class, renderer_class) tuples."""
    return list(_renderer_registry.items())


def clear_renderer_cache():
    """Clear all cached renderer instances (useful for testing)."""
    _renderer_cache.clear()


# ---------------------------------------------------------------------------
# Skia backend registry (parallel to the drawsvg registry above)
#
# Lives here, alongside @renderer, because it must be importable WITHOUT pulling
# in the optional `skia` package: a state declares its Skia renderer with a
# dotted "module:Class" path that is imported only when the Skia backend
# resolves it. Importing this module never imports skia.
# ---------------------------------------------------------------------------

# Maps state class → dotted "module:Class" path, or the resolved renderer class
# once first looked up.
_skia_registry: dict[Type, "str | Type"] = {}

# Singleton cache for stateless skia renderer instances
_skia_cache: dict[Type, Any] = {}

# Sentinel a state's get_skia_renderer_class() may return to declare itself
# explicitly unsupported by the Skia backend, short-circuiting the MRO walk that
# would otherwise inherit a base class's renderer. check_scene then reports it
# and the scene falls back to the SVG route.
SKIA_UNSUPPORTED: Any = object()


def skia_renderer(path: str):
    """Decorator placed ON A STATE CLASS to assign its default Skia renderer.

    ``path`` is a dotted "module:Class" import string, resolved lazily on first
    use so importing the state never imports the optional ``skia`` package.

    Example:
        @skia_renderer("svan2d.primitive.renderer.skia.circle:CircleSkiaRenderer")
        @renderer(CircleRenderer)
        @dataclass(frozen=True)
        class CircleState(VertexState):
            ...
    """

    def decorator(state_class: Type) -> Type:
        if state_class in _skia_registry:
            raise RuntimeError(
                f"State '{state_class.__name__}' already has a Skia renderer "
                f"({_skia_registry[state_class]!r})."
            )
        _skia_registry[state_class] = path
        return state_class

    return decorator


def _resolve_skia(entry: "str | Type") -> Type:
    """Import a dotted "module:Class" path to a class; pass classes through."""
    if isinstance(entry, str):
        module_path, _, attr = entry.partition(":")
        return getattr(importlib.import_module(module_path), attr)
    return entry


def get_skia_renderer_class_for_state(state: Any) -> Type | None:
    """Resolve the Skia renderer class for a state, or None if unregistered.

    Walks the state's MRO so subclasses inherit a base class's renderer. State
    subclasses may override ``get_skia_renderer_class()`` to bypass the registry.
    """
    override = state.get_skia_renderer_class()
    if override is SKIA_UNSUPPORTED:
        return None
    if override is not None:
        return override
    for klass in type(state).__mro__:
        entry = _skia_registry.get(klass)
        if entry is not None:
            renderer_class = _resolve_skia(entry)
            _skia_registry[klass] = renderer_class  # cache resolved class
            return renderer_class
    return None


def get_skia_renderer_for_state(state: Any) -> Any:
    """Return a cached Skia renderer instance for the state, or None.

    A state mid-morph carries _aligned_contours; the SVG path renders such
    states via VertexRenderer, so the Skia path uses VertexSkiaRenderer to match.
    """
    if getattr(state, "_aligned_contours", None) is not None:
        from svan2d.primitive.renderer.skia.base_vertex import VertexSkiaRenderer

        renderer_class = VertexSkiaRenderer
    else:
        renderer_class = get_skia_renderer_class_for_state(state)
    if renderer_class is None:
        return None
    inst = _skia_cache.get(renderer_class)
    if inst is None:
        inst = renderer_class()
        _skia_cache[renderer_class] = inst
    return inst