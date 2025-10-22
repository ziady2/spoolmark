"""Batch operations for importing, inspecting, and validating tracks.

The functions in this module deliberately keep the batch layer small: parsers
remain responsible for understanding subtitle formats, :class:`Track` remains
the data model, and this module adds ordering and failure isolation around
those APIs.

``batch_import`` returns a :class:`BatchImportResult`.  It behaves like a
regular ``list[Track]`` so its value can be passed directly to
``batch_stats`` or ``batch_validate``.  In addition, its ``records`` attribute
contains one record per requested file and ``errors`` contains the failed
records.  This makes partial success useful without silently losing failures.
"""

from __future__ import annotations

import codecs
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableSequence, Optional, Tuple, Union

from .ass_import import parse_ass_text
from .json_import import parse_json_text
from .srt_import import parse_srt_text
from .stats import track_stats
from .track import Track
from .txt_import import parse_txt_text
from .vtt_import import parse_vtt_text

Pathish = Union[str, os.PathLike]
ImportRecord = Dict[str, Any]

SUPPORTED_FORMATS: Tuple[str, ...] = ("ass", "json", "srt", "txt", "vtt")

_FORMAT_ALIASES: Mapping[str, str] = {
    "ass": "ass",
    "json": "json",
    "srt": "srt",
    "ssa": "ass",
    "subrip": "srt",
    "text": "txt",
    "txt": "txt",
    "vtt": "vtt",
    "webvtt": "vtt",
}

_TEXT_PARSERS = {
    "ass": parse_ass_text,
    "json": parse_json_text,
    "srt": parse_srt_text,
    "txt": parse_txt_text,
    "vtt": parse_vtt_text,
}


class BatchImportResult(List[Track]):
    """Successful tracks plus a complete per-file import ledger.

    The object intentionally subclasses ``list`` for backwards-compatible,
    unsurprising use::

        tracks = batch_import(paths)
        for track in tracks:
            ...

    ``records`` follows the original input order.  Every record has ``path``,
    ``format``, ``ok``, ``track``, ``error``, and ``error_type`` keys.
    ``errors`` is the ordered subset for which ``ok`` is false.
    """

    def __init__(
        self,
        tracks: Iterable[Track] = (),
        *,
        records: Iterable[ImportRecord] = (),
    ) -> None:
        super().__init__(tracks)
        self.records: List[ImportRecord] = list(records)
        self.errors: List[ImportRecord] = [record for record in self.records if not record["ok"]]

    @property
    def succeeded(self) -> int:
        """Number of files imported successfully."""
        return len(self)

    @property
    def failed(self) -> int:
        """Number of files that could not be imported."""
        return len(self.errors)

    @property
    def ok(self) -> bool:
        """Whether every requested file imported successfully."""
        return not self.errors


def _normalise_format(value: str) -> str:
    """Return the canonical form of a user-supplied format name."""
    if not isinstance(value, str):
        raise TypeError("format must be a string")
    key = value.strip().lower().lstrip(".")
    canonical = _FORMAT_ALIASES.get(key)
    if canonical is None:
        choices = ", ".join(SUPPORTED_FORMATS)
        raise ValueError(f"unsupported subtitle format {value!r}; choose from {choices}")
    return canonical


def infer_format(path: Pathish) -> str:
    """Infer a supported subtitle format from *path*'s final suffix.

    Matching is case-insensitive and ``.ssa`` is treated as ASS.  A
    :class:`ValueError` is raised when there is no supported suffix; content
    sniffing is intentionally avoided so the result is deterministic.
    """
    try:
        raw_path = os.fspath(path)
    except TypeError as exc:
        raise TypeError("path must be a string or path-like object") from exc
    if isinstance(raw_path, bytes):
        raw_path = os.fsdecode(raw_path)
    suffix = Path(raw_path).suffix
    if not suffix:
        raise ValueError(f"cannot infer subtitle format for {raw_path!r}: no file extension")
    try:
        return _normalise_format(suffix)
    except ValueError as exc:
        raise ValueError(
            f"cannot infer subtitle format for {raw_path!r}: unsupported extension {suffix!r}"
        ) from exc


def _as_path_list(paths: Iterable[Pathish]) -> Iterable[Pathish]:
    """Treat a single string/path as one item, not an iterable of characters."""
    if isinstance(paths, (str, bytes, os.PathLike)):
        return (paths,)
    try:
        return iter(paths)
    except TypeError as exc:
        raise TypeError("paths must be a path or an iterable of paths") from exc


def _selected_format(
    format_name: Optional[str],
    fmt: Optional[str],
) -> Optional[str]:
    """Resolve the long and short names for the format override."""
    long_value = _normalise_format(format_name) if format_name is not None else None
    short_value = _normalise_format(fmt) if fmt is not None else None
    if long_value is not None and short_value is not None and long_value != short_value:
        raise ValueError("format and fmt specify different subtitle formats")
    return long_value if long_value is not None else short_value


def _path_text(path: Pathish) -> Tuple[str, Path]:
    """Return a stable display path and a :class:`Path` object."""
    raw_path = os.fspath(path)
    if isinstance(raw_path, bytes):
        raw_path = os.fsdecode(raw_path)
    return raw_path, Path(raw_path)


def _error_record(path: str, format_name: Optional[str], exc: Exception) -> ImportRecord:
    return {
        "path": path,
        "format": format_name,
        "ok": False,
        "track": None,
        "error": str(exc) or exc.__class__.__name__,
        "error_type": exc.__class__.__name__,
    }


def _success_record(path: str, format_name: str, track: Track) -> ImportRecord:
    return {
        "path": path,
        "format": format_name,
        "ok": True,
        "track": track,
        "error": None,
        "error_type": None,
    }


def batch_import(
    paths: Iterable[Pathish],
    format: Optional[str] = None,
    *,
    fmt: Optional[str] = None,
    encoding: str = "utf-8-sig",
    on_error: str = "collect",
    strict: bool = False,
    errors: Optional[MutableSequence[ImportRecord]] = None,
) -> BatchImportResult:
    """Import multiple subtitle files while preserving input order.

    Parameters
    ----------
    paths:
        A path or iterable of paths.  Generators and duplicate paths are
        supported and are processed exactly once in the order supplied.
    format / fmt:
        Optional format override applied to every file.  With neither set,
        the format is inferred independently from each filename.  ``fmt`` is
        a concise alias for callers that prefer not to shadow ``format``.
    encoding:
        Text encoding used for every input file.  The default also consumes a
        UTF-8 byte-order mark when present.
    on_error:
        ``"collect"`` (the default) records a failure and continues;
        ``"raise"`` propagates the first failure immediately.
    strict:
        Compatibility shortcut for ``on_error="raise"``.
    errors:
        Optional mutable sequence extended with the same failure records held
        by the returned object's ``errors`` attribute.

    Returns
    -------
    BatchImportResult
        A list-like sequence of successful tracks.  Partial failures are
        available through ``result.errors`` and all attempts through
        ``result.records``.

    Notes
    -----
    An invalid global option (unknown format, encoding, or error policy) is a
    caller error and is raised before processing.  Per-file path, decoding,
    and parse failures are isolated when ``on_error="collect"``.
    """
    if not isinstance(encoding, str) or not encoding.strip():
        raise ValueError("encoding must be a non-empty string")
    try:
        codecs.lookup(encoding)
    except LookupError as exc:
        raise ValueError(f"unknown text encoding {encoding!r}") from exc
    if on_error not in {"collect", "raise"}:
        raise ValueError("on_error must be 'collect' or 'raise'")
    if not isinstance(strict, bool):
        raise TypeError("strict must be a boolean")
    if errors is not None and not callable(getattr(errors, "append", None)):
        raise TypeError("errors must be a mutable sequence")
    if strict:
        on_error = "raise"

    override = _selected_format(format, fmt)
    tracks: List[Track] = []
    records: List[ImportRecord] = []

    for supplied_path in _as_path_list(paths):
        display_path = repr(supplied_path)
        path_obj: Optional[Path] = None
        selected = override
        try:
            display_path, path_obj = _path_text(supplied_path)
            if selected is None:
                selected = infer_format(path_obj)
            text = path_obj.read_text(encoding=encoding)
            parser = _TEXT_PARSERS[selected]
            track = parser(text, name=path_obj.stem)
        except Exception as exc:
            if on_error == "raise":
                raise
            record = _error_record(display_path, selected, exc)
            records.append(record)
            if errors is not None:
                errors.append(record)
            continue

        tracks.append(track)
        records.append(_success_record(display_path, selected, track))

    return BatchImportResult(tracks, records=records)


def _iter_tracks(tracks: Iterable[Track]) -> Iterable[Track]:
    """Yield tracks with a useful error for malformed batches."""
    try:
        iterator = iter(tracks)
    except TypeError as exc:
        raise TypeError("tracks must be an iterable of Track objects") from exc
    for index, track in enumerate(iterator):
        if not isinstance(track, Track):
            raise TypeError(f"tracks[{index}] must be a Track, got {type(track).__name__}")
        yield track


def batch_stats(tracks: Iterable[Track]) -> List[Dict[str, Any]]:
    """Return one statistical summary per track in input order.

    The numerical fields come from :func:`subcue.stats.track_stats`; ``name``
    and ``language`` are included so rows remain identifiable after export.
    Empty input returns an empty list and an empty track produces the normal
    zero-valued stats row.
    """
    rows: List[Dict[str, Any]] = []
    for track in _iter_tracks(tracks):
        row: Dict[str, Any] = {
            "name": track.name,
            "language": track.language,
        }
        row.update(track_stats(track))
        rows.append(row)
    return rows


def _positive_threshold(value: Any, name: str, *, allow_zero: bool = False) -> float:
    """Validate numeric batch-validation thresholds."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number")
    number = float(value)
    minimum_ok = number >= 0 if allow_zero else number > 0
    if not math.isfinite(number) or not minimum_ok:
        operator = ">=" if allow_zero else ">"
        raise ValueError(f"{name} must be finite and {operator} 0")
    return number


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be > 0")
    return value


def batch_validate(
    tracks: Iterable[Track],
    max_cps: float = 20.0,
    *,
    min_duration: float = 0.7,
    max_duration: float = 7.0,
    max_lines: int = 2,
    max_chars_per_line: int = 42,
    min_gap: float = 0.04,
    max_line_length: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Run diagnostics for each track and return ordered result rows.

    ``valid`` is true only when no diagnostic issues were found, including
    warnings.  The detailed ``issues`` are retained per track, while severity
    counts make common batch-level filtering inexpensive.
    """
    max_cps_value = _positive_threshold(max_cps, "max_cps")
    min_duration_value = _positive_threshold(min_duration, "min_duration", allow_zero=True)
    max_duration_value = _positive_threshold(max_duration, "max_duration")
    min_gap_value = _positive_threshold(min_gap, "min_gap", allow_zero=True)
    max_lines_value = _positive_integer(max_lines, "max_lines")
    max_chars_value = _positive_integer(max_chars_per_line, "max_chars_per_line")
    if max_line_length is not None:
        alias_value = _positive_integer(max_line_length, "max_line_length")
        if max_chars_per_line != 42 and alias_value != max_chars_value:
            raise ValueError("max_chars_per_line and max_line_length specify different limits")
        max_chars_value = alias_value
    if max_duration_value < min_duration_value:
        raise ValueError("max_duration must be greater than or equal to min_duration")

    # Imported lazily so importing subcue.batch never makes diagnostics a
    # prerequisite for format parsing alone.
    from .diagnostic import run_diagnostics

    rows: List[Dict[str, Any]] = []
    for track in _iter_tracks(tracks):
        issues = run_diagnostics(
            track,
            max_cps=max_cps_value,
            min_duration=min_duration_value,
            max_duration=max_duration_value,
            max_lines=max_lines_value,
            max_chars_per_line=max_chars_value,
            min_gap=min_gap_value,
        )
        error_count = sum(issue.get("severity") == "error" for issue in issues)
        warning_count = sum(issue.get("severity") == "warning" for issue in issues)
        info_count = sum(issue.get("severity") == "info" for issue in issues)
        rows.append(
            {
                "name": track.name,
                "track_name": track.name,
                "cue_count": len(track),
                "valid": not issues,
                "issue_count": len(issues),
                "error_count": error_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "issues": issues,
            }
        )
    return rows


__all__ = [
    "BatchImportResult",
    "SUPPORTED_FORMATS",
    "batch_import",
    "batch_stats",
    "batch_validate",
    "infer_format",
]
