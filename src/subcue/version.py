"""Version information for subcue."""

from __future__ import annotations

__version__ = "0.12.1"
VERSION_INFO: tuple[int, ...] = tuple(int(x) for x in __version__.split("."))


def version_string() -> str:
    major, minor, patch = VERSION_INFO
    return f"subcue {major}.{minor}.{patch}"


def version_tuple() -> tuple[int, int, int]:
    return (VERSION_INFO[0], VERSION_INFO[1], VERSION_INFO[2])


def check_python_version(minimum: tuple[int, int] = (3, 9)) -> bool:
    import sys

    return sys.version_info[:2] >= minimum


def build_user_agent() -> str:
    import platform

    py = platform.python_version()
    return f"subcue/{__version__} python/{py} os/{platform.system().lower()}"
