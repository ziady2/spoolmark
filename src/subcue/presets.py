"""Preset configurations for common subtitle standards."""

from __future__ import annotations

from typing import Any

from .errors import NotFoundError


def _make_preset(
    name: str,
    *,
    max_cps: float,
    max_line_length: int,
    max_lines: int,
    min_duration: float,
    max_duration: float,
    min_gap: float,
) -> dict[str, Any]:
    """Build a preset dict with standard keys."""
    return {
        "name": name,
        "max_cps": max_cps,
        "max_line_length": max_line_length,
        "max_lines": max_lines,
        "min_duration": min_duration,
        "max_duration": max_duration,
        "min_gap": min_gap,
    }


def netflix_preset() -> dict[str, Any]:
    """Return the Netflix Timed Text Style Guide preset.

    Enforces 17 cps, 42-char lines, 2 lines max, and 5/7s durations.
    """
    return _make_preset(
        "netflix",
        max_cps=17.0,
        max_line_length=42,
        max_lines=2,
        min_duration=0.833,
        max_duration=7.0,
        min_gap=0.083,
    )


def broadcast_preset() -> dict[str, Any]:
    """Return a generic broadcast subtitle preset.

    Typical broadcast rules: 20 cps, 37-char lines, 2 lines.
    """
    return _make_preset(
        "broadcast",
        max_cps=20.0,
        max_line_length=37,
        max_lines=2,
        min_duration=1.0,
        max_duration=6.0,
        min_gap=0.1,
    )


def web_preset() -> dict[str, Any]:
    """Return a relaxed preset suitable for web video.

    Higher CPS and longer lines are tolerated.
    """
    return _make_preset(
        "web",
        max_cps=25.0,
        max_line_length=60,
        max_lines=3,
        min_duration=0.5,
        max_duration=10.0,
        min_gap=0.0,
    )


_BUILTINS: dict[str, Any] = {
    "netflix": netflix_preset,
    "broadcast": broadcast_preset,
    "web": web_preset,
}


def list_presets() -> list[str]:
    """Return a sorted list of available preset names."""
    return sorted(_BUILTINS.keys())


def get_preset(name: str) -> dict[str, Any]:
    """Retrieve a preset by *name*.

    Parameters
    ----------
    name:
        One of the built-in preset names (see :func:`list_presets`).

    Raises
    ------
    NotFoundError
        When *name* does not match any registered preset.
    """
    factory = _BUILTINS.get(name)
    if factory is None:
        raise NotFoundError("preset", name)
    return factory()
