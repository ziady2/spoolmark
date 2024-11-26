"""Application configuration for subcue."""

from __future__ import annotations

import codecs
import json
import math
import os
from pathlib import Path
from typing import Any

from .errors import ConfigError

DEFAULT_CONFIG: dict[str, Any] = {
    "data_dir": "~/.subcue",
    "default_fps": 24.0,
    "max_cps": 25.0,
    "min_duration": 0.7,
    "max_duration": 7.0,
    "min_gap": 0.04,
    "default_format": "srt",
    "encoding": "utf-8",
    "line_length": 42,
    "max_lines": 2,
    "color_output": True,
    "locale": "en",
}

_VALID_FORMATS = {"srt", "vtt", "ass", "json", "txt", "csv", "html"}


class Config:
    __slots__ = ("_data", "_path")

    def __init__(self, data: dict[str, Any] | None = None, path: str = "") -> None:
        base = dict(DEFAULT_CONFIG)
        if data is not None and not isinstance(data, dict):
            raise ConfigError("config", "must be a JSON-style object")
        if data:
            if any(not isinstance(key, str) for key in data):
                raise ConfigError("config", "keys must be strings")
            base.update(data)
        self._data: dict[str, Any] = base
        self._path: str = path

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        if key not in self._data:
            raise ConfigError(key, "not found")
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        return f"Config(keys={sorted(self._data)})"

    def keys(self) -> list[str]:
        return sorted(self._data)

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def with_override(self, key: str, value: Any) -> "Config":
        new_data = dict(self._data)
        new_data[key] = value
        return Config(new_data, path=self._path)

    @property
    def max_cps(self) -> float:
        return float(self._data.get("max_cps", 25.0))

    @property
    def min_duration(self) -> float:
        return float(self._data.get("min_duration", 0.7))

    @property
    def max_duration(self) -> float:
        return float(self._data.get("max_duration", 7.0))


def load_config(path: str | Path = "") -> Config:
    if not path:
        path = Path(os.path.expanduser("~/.subcue/config.json"))
    else:
        path = Path(path)
    data: dict[str, Any] = {}
    if path.is_file():
        try:
            raw = path.read_text(encoding="utf-8").strip()
            if raw:
                decoded = json.loads(raw)
                if not isinstance(decoded, dict):
                    raise ConfigError("config_file", "top-level JSON value must be an object")
                data = decoded
        except (json.JSONDecodeError, OSError, UnicodeError) as exc:
            raise ConfigError("config_file", str(exc)) from exc
    return Config(data, path=str(path))


def save_config(cfg: Config, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg.to_dict(), indent=2) + "\n", encoding="utf-8")


def validate_config(cfg: Config) -> list[str]:
    """Return human-readable warnings for values outside the supported schema."""
    warnings: list[str] = []
    data = cfg.to_dict()
    unknown = sorted(set(data) - set(DEFAULT_CONFIG))
    for key in unknown:
        warnings.append(f"unknown configuration key {key!r}")

    fmt = cfg.get("default_format", "srt")
    if not isinstance(fmt, str) or fmt not in _VALID_FORMATS:
        warnings.append(f"default_format {fmt!r} not in {sorted(_VALID_FORMATS)}")

    def valid_number(key: str, *, allow_zero: bool) -> bool:
        value = cfg.get(key)
        valid = not isinstance(value, bool) and isinstance(value, (int, float))
        if valid:
            try:
                numeric_value = float(value)
            except (OverflowError, TypeError, ValueError):
                valid = False
            else:
                valid = math.isfinite(numeric_value) and (
                    numeric_value >= 0 if allow_zero else numeric_value > 0
                )
        if not valid:
            qualifier = "non-negative" if allow_zero else "positive"
            warnings.append(f"{key} must be a finite {qualifier} number, got {value!r}")
        return valid

    valid_number("default_fps", allow_zero=False)
    valid_number("max_cps", allow_zero=False)
    min_duration_valid = valid_number("min_duration", allow_zero=True)
    max_duration_valid = valid_number("max_duration", allow_zero=False)
    valid_number("min_gap", allow_zero=True)
    if (
        min_duration_valid
        and max_duration_valid
        and cfg.get("max_duration") < cfg.get("min_duration")
    ):
        warnings.append("max_duration must be greater than or equal to min_duration")

    for key in ("line_length", "max_lines"):
        value = cfg.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            warnings.append(f"{key} must be a positive integer, got {value!r}")

    color_output = cfg.get("color_output")
    if not isinstance(color_output, bool):
        warnings.append(f"color_output must be a boolean, got {color_output!r}")

    for key in ("data_dir", "locale"):
        value = cfg.get(key)
        if not isinstance(value, str) or not value.strip():
            warnings.append(f"{key} must be a non-empty string, got {value!r}")

    encoding = cfg.get("encoding")
    if not isinstance(encoding, str) or not encoding.strip():
        warnings.append(f"encoding must be a recognised non-empty codec, got {encoding!r}")
    else:
        try:
            codecs.lookup(encoding)
        except LookupError:
            warnings.append(f"encoding must be a recognised non-empty codec, got {encoding!r}")
    return warnings
