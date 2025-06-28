"""High-level subtitle file loading, format detection, and serialisation.

The format-specific modules intentionally stay small and focused.  This module
provides the common boundary used by command-line and batch workflows: it
normalises format names, decodes files, dispatches parsers, renders supported
outputs, and writes files atomically.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

from .ass_import import parse_ass_text
from .csv_export import export_track_csv
from .cue import Cue
from .errors import FormatError, ParseError
from .html_writer import render_track_preview
from .json_import import parse_json_text, track_to_json
from .srt_import import cues_to_srt, parse_srt_text
from .timing import format_timecode_ass
from .track import Track
from .txt_import import cues_to_txt, parse_txt_text
from .vtt_import import cues_to_vtt, parse_vtt_text

INPUT_FORMATS: tuple[str, ...] = ("srt", "vtt", "ass", "json", "txt")
OUTPUT_FORMATS: tuple[str, ...] = INPUT_FORMATS + ("csv", "html")

_FORMAT_ALIASES = {
    "subrip": "srt",
    "webvtt": "vtt",
    "ssa": "ass",
    "text": "txt",
    "htm": "html",
}
_EXTENSION_FORMATS = {
    ".srt": "srt",
    ".vtt": "vtt",
    ".ass": "ass",
    ".ssa": "ass",
    ".json": "json",
    ".txt": "txt",
    ".text": "txt",
    ".csv": "csv",
    ".html": "html",
    ".htm": "html",
}
_TIMECODE_ARROW = re.compile(r"\d+:\d{2}:\d{2}[,.]\d{1,3}\s*-->\s*" r"\d+:\d{2}:\d{2}[,.]\d{1,3}")


def normalize_format(format_name: str, *, for_output: bool = False) -> str:
    """Return a canonical lower-case format name.

    Leading dots are accepted so callers can pass either ``"srt"`` or
    ``".srt"``.  A small set of common aliases is supported.  ``FormatError``
    is raised when the name is empty or not supported for the requested
    direction.
    """
    value = str(format_name).strip().lower().lstrip(".")
    value = _FORMAT_ALIASES.get(value, value)
    allowed = OUTPUT_FORMATS if for_output else INPUT_FORMATS
    if value not in allowed:
        direction = "output" if for_output else "input"
        choices = ", ".join(allowed)
        raise FormatError(
            f"unsupported {direction} format {format_name!r}; choose one of: {choices}"
        )
    return value


def format_from_path(path: str | Path, *, for_output: bool = False) -> str:
    """Infer a canonical format from a filename extension."""
    suffix = Path(path).suffix.lower()
    format_name = _EXTENSION_FORMATS.get(suffix)
    if format_name is None:
        label = suffix or "(none)"
        raise FormatError(f"cannot infer subtitle format from extension {label!r}")
    return normalize_format(format_name, for_output=for_output)


def detect_format(text: str, *, filename: str | Path | None = None) -> str:
    """Detect an input format using a filename and conservative content hints.

    A recognised filename extension wins.  Content detection is primarily for
    stdin and extensionless files and deliberately avoids treating arbitrary
    prose as a structured subtitle format.
    """
    if filename is not None and Path(filename).suffix:
        try:
            return format_from_path(filename)
        except FormatError:
            pass

    sample = text.lstrip("\ufeff \t\r\n")
    upper = sample[:512].upper()
    if upper.startswith("WEBVTT"):
        return "vtt"
    if (
        upper.startswith("[SCRIPT INFO]")
        or "\n[EVENTS]" in upper
        or re.search(r"(?m)^DIALOGUE:\s*", sample, re.IGNORECASE)
    ):
        return "ass"
    if sample.startswith(("{", "[")):
        try:
            decoded = json.loads(sample)
        except (json.JSONDecodeError, TypeError):
            pass
        else:
            if isinstance(decoded, list) or (isinstance(decoded, dict) and "cues" in decoded):
                return "json"
    if _TIMECODE_ARROW.search(sample):
        return "srt"
    if re.search(r"(?m)^\s*\d[\d:.,-]+\s*(?:-->|->|\|)", sample):
        return "txt"
    raise FormatError("could not detect subtitle format from content")


def parse_track(text: str, format_name: str, *, name: str = "") -> Track:
    """Parse subtitle *text* using an explicit input format."""
    canonical = normalize_format(format_name)
    track_name = name.strip() or f"{canonical.upper()} Track"
    parsers = {
        "srt": parse_srt_text,
        "vtt": parse_vtt_text,
        "ass": parse_ass_text,
        "json": parse_json_text,
        "txt": parse_txt_text,
    }
    return parsers[canonical](text, name=track_name)


def decode_subtitle_bytes(
    data: bytes,
    *,
    encoding: str = "auto",
    fallback_encodings: Sequence[str] = ("utf-16", "cp1252"),
) -> tuple[str, str]:
    """Decode subtitle bytes and return ``(text, encoding_used)``.

    Automatic decoding prefers UTF-8 (including BOM), then optional explicit
    fallbacks.  Latin-1 is not used implicitly because it never fails and can
    silently turn a corrupt UTF-8 file into plausible but damaged text.
    """
    requested = encoding.strip().lower()
    if requested != "auto":
        try:
            return data.decode(encoding), encoding
        except (LookupError, UnicodeDecodeError) as exc:
            raise ParseError(f"cannot decode input using {encoding!r}: {exc}") from exc

    candidates: list[str] = ["utf-8-sig"]
    has_utf16_bom = data.startswith((b"\xff\xfe", b"\xfe\xff"))
    for item in fallback_encodings:
        normalised = item.lower().replace("_", "-")
        if normalised == "utf-16" and not has_utf16_bom:
            continue
        if item not in candidates:
            candidates.append(item)
    failures: list[str] = []
    for candidate in candidates:
        try:
            return data.decode(candidate), candidate
        except (LookupError, UnicodeDecodeError) as exc:
            failures.append(f"{candidate}: {exc}")
    tried = "; ".join(failures)
    raise ParseError(f"cannot decode subtitle bytes ({tried})")


def load_track(
    path: str | Path,
    *,
    format_name: str | None = None,
    encoding: str = "auto",
    fallback_encodings: Sequence[str] = ("utf-16", "cp1252"),
    name: str | None = None,
) -> Track:
    """Load a subtitle track from disk.

    ``format_name`` overrides extension/content detection.  Read and decode
    failures are translated to ``ParseError`` so callers have one predictable
    error family to handle.
    """
    source = Path(path)
    if not source.exists():
        raise ParseError(f"file not found: {source}")
    if not source.is_file():
        raise ParseError(f"not a file: {source}")
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise ParseError(f"cannot read file {source}: {exc}") from exc
    text, _ = decode_subtitle_bytes(
        data,
        encoding=encoding,
        fallback_encodings=fallback_encodings,
    )
    canonical = (
        normalize_format(format_name)
        if format_name is not None
        else detect_format(text, filename=source)
    )
    return parse_track(text, canonical, name=name or source.stem)


def serialize_track(
    track: Track,
    format_name: str,
    *,
    json_indent: int | None = 2,
    include_csv_metadata: bool = True,
) -> str:
    """Serialise a track to one of the supported output formats."""
    canonical = normalize_format(format_name, for_output=True)
    if canonical == "srt":
        return cues_to_srt(track.cues)
    if canonical == "vtt":
        return cues_to_vtt(track.cues)
    if canonical == "ass":
        return cues_to_ass(track.cues, title=track.name)
    if canonical == "json":
        return track_to_json(track, indent=json_indent) + "\n"
    if canonical == "txt":
        return cues_to_txt(track.cues)
    if canonical == "csv":
        return export_track_csv(track, include_meta=include_csv_metadata)
    if canonical == "html":
        return render_track_preview(track) + "\n"
    raise AssertionError(f"unhandled output format: {canonical}")


def cues_to_ass(cues: Iterable[Cue], *, title: str = "Subcue Export") -> str:
    """Serialise cues as a minimal, standards-compatible ASS document."""
    cue_list = list(cues)
    safe_title = _ass_field(title) or "Subcue Export"
    style_names = ["Default"]
    seen_styles = {"default"}
    for cue in cue_list:
        style_name = _ass_field(cue.style) or "Default"
        canonical = style_name.casefold()
        if canonical not in seen_styles:
            seen_styles.add(canonical)
            style_names.append(style_name)
    lines = [
        "[Script Info]",
        f"Title: {safe_title}",
        "ScriptType: v4.00+",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "YCbCr Matrix: TV.601",
        "",
        "[V4+ Styles]",
        (
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding"
        ),
    ]
    lines.extend(
        "Style: "
        f"{style_name},Arial,20,&H00FFFFFF,&H000000FF,&H00000000,"
        "&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1"
        for style_name in style_names
    )
    lines.extend(
        [
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]
    )
    for cue in cue_list:
        style = _ass_field(cue.style) or "Default"
        speaker = _ass_field(cue.speaker)
        text = cue.text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\n", r"\N")
        lines.append(
            "Dialogue: 0,"
            f"{format_timecode_ass(cue.start)},"
            f"{format_timecode_ass(cue.end)},"
            f"{style},{speaker},0,0,0,,{text}"
        )
    return "\n".join(lines) + "\n"


def write_track(
    track: Track,
    path: str | Path,
    *,
    format_name: str | None = None,
    encoding: str = "utf-8",
    overwrite: bool = False,
) -> Path:
    """Atomically serialise *track* to *path* and return the final path.

    Existing files are protected unless ``overwrite=True``.  The temporary
    file is created beside the destination so ``os.replace`` stays on the same
    filesystem and is atomic on supported platforms.
    """
    destination = Path(path)
    canonical = (
        normalize_format(format_name, for_output=True)
        if format_name is not None
        else format_from_path(destination, for_output=True)
    )
    if destination.exists() and not overwrite:
        raise FormatError(f"output file already exists: {destination}")
    if destination.exists() and not destination.is_file():
        raise FormatError(f"output path is not a file: {destination}")
    parent = destination.parent
    if not parent.exists():
        raise FormatError(f"output directory does not exist: {parent}")

    rendered = serialize_track(track, canonical)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            newline="\n",
            dir=str(parent),
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        if overwrite:
            os.replace(temp_path, destination)
        else:
            # A hard link publishes the fully-written temporary file without
            # ever replacing a destination created by another process between
            # our initial check and this point.
            os.link(temp_path, destination)
            temp_path.unlink()
        temp_path = None
    except FileExistsError as exc:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise FormatError(f"output file already exists: {destination}") from exc
    except (LookupError, OSError, UnicodeError) as exc:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise FormatError(f"cannot write output file {destination}: {exc}") from exc
    return destination


def suggested_output_path(
    source: str | Path,
    format_name: str,
    *,
    suffix_label: str = "",
) -> Path:
    """Build a sibling output path for a source and target format."""
    canonical = normalize_format(format_name, for_output=True)
    extension = ".ass" if canonical == "ass" else f".{canonical}"
    source_path = Path(source)
    stem = source_path.stem
    if suffix_label:
        clean_label = re.sub(r"[^A-Za-z0-9_.-]+", "-", suffix_label).strip("-.")
        if clean_label:
            stem = f"{stem}-{clean_label}"
    return source_path.with_name(stem + extension)


def _ass_field(value: str) -> str:
    """Sanitise a value used in a comma-delimited ASS field."""
    return str(value).replace(",", " ").replace("\r", " ").replace("\n", " ").strip()
