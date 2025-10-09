"""Simple plugin registry for extensible processing pipelines."""

from __future__ import annotations

from typing import Any, Protocol

from .errors import DuplicateError, NotFoundError


class PluginFunc(Protocol):
    """Protocol for a callable accepted as a plugin."""

    def __call__(self, data: Any, **kwargs: Any) -> Any: ...


_REGISTRY: dict[str, PluginFunc] = {}


def register(name: str, func: PluginFunc) -> None:
    """Register a plugin function under *name*.

    Raises :class:`DuplicateError` if the name is already registered.

    Parameters
    ----------
    name:
        Unique plugin identifier.
    func:
        Callable conforming to :class:`PluginFunc`.
    """
    if name in _REGISTRY:
        raise DuplicateError("plugin", name)
    _REGISTRY[name] = func


def unregister(name: str) -> None:
    """Remove a previously registered plugin.

    Raises :class:`NotFoundError` if the name is not registered.
    """
    if name not in _REGISTRY:
        raise NotFoundError("plugin", name)
    del _REGISTRY[name]


def get_plugin(name: str) -> PluginFunc:
    """Retrieve a registered plugin by *name*.

    Raises :class:`NotFoundError` if not found.
    """
    if name not in _REGISTRY:
        raise NotFoundError("plugin", name)
    return _REGISTRY[name]


def list_plugins() -> list[str]:
    """Return a sorted list of all registered plugin names."""
    return sorted(_REGISTRY.keys())


def clear() -> None:
    """Remove all registered plugins."""
    _REGISTRY.clear()


def run_plugin(name: str, data: Any, **kwargs: Any) -> Any:
    """Execute the plugin *name* with *data* and optional keyword arguments.

    Parameters
    ----------
    name:
        Registered plugin identifier.
    data:
        Primary input to pass to the plugin callable.
    **kwargs:
        Extra keyword arguments forwarded to the plugin.

    Returns
    -------
    Any
        The return value of the plugin callable.
    """
    func = get_plugin(name)
    return func(data, **kwargs)


def run_pipeline(
    names: list[str],
    data: Any,
    **kwargs: Any,
) -> Any:
    """Run multiple plugins in sequence, piping output to input.

    Parameters
    ----------
    names:
        Ordered plugin identifiers to execute.
    data:
        Initial input data.

    Returns
    -------
    Any
        Output of the last plugin in the pipeline.
    """
    result = data
    for name in names:
        result = run_plugin(name, result, **kwargs)
    return result
