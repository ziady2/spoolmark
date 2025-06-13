"""CSV export utilities for tracks and cues."""

from __future__ import annotations

import csv
import io
from typing import Sequence

from .cue import Cue
from .track import Track

_CUE_FIELDS = ("index", "start", "end", "text", "speaker", "style")
_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _safe_cell(value: object) -> str:
    """Return a spreadsheet-safe string while preserving ordinary values."""
    if value is None:
        return ""
    rendered = str(value)
    if isinstance(value, str) and rendered.lstrip().startswith(_FORMULA_PREFIXES):
        return "'" + rendered
    return rendered


def _single_line(value: str) -> str:
    """Keep comment-style metadata on exactly one physical CSV line."""
    return " ".join(value.replace("\r", "\n").splitlines()).strip()


def _cue_row(cue: Cue, fields: Sequence[str]) -> dict[str, str]:
    """Extract a dict of string values from a *Cue* for the given *fields*."""
    out: dict[str, str] = {}
    for f in fields:
        val = getattr(cue, f, "")
        out[f] = _safe_cell(val)
    return out


def export_cues_csv(
    cues: Sequence[Cue],
    *,
    fields: Sequence[str] | None = None,
    delimiter: str = ",",
) -> str:
    """Export cues to a CSV string.

    Parameters
    ----------
    cues:
        Cue objects to export.
    fields:
        Column names to include (defaults to standard cue fields).
    delimiter:
        Field delimiter character.
    """
    cols = list(fields) if fields else list(_CUE_FIELDS)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols, delimiter=delimiter)
    csv.writer(buf, delimiter=delimiter).writerow([_safe_cell(column) for column in cols])
    for c in cues:
        writer.writerow(_cue_row(c, cols))
    return buf.getvalue()


def export_track_csv(
    track: Track,
    *,
    fields: Sequence[str] | None = None,
    include_meta: bool = True,
) -> str:
    """Export a full track to CSV including optional metadata header.

    When *include_meta* is ``True`` the track name and language are
    written as comment lines before the data rows.
    """
    parts: list[str] = []
    if include_meta:
        parts.append(f"# name: {_single_line(track.name) or 'untitled'}")
        parts.append(f"# language: {_single_line(track.language) or 'unknown'}")
        parts.append("")
    body = export_cues_csv(track.cues, fields=fields)
    parts.append(body)
    return "\n".join(parts)


def export_rows_csv(
    rows: Sequence[dict[str, object]],
    *,
    columns: Sequence[str] | None = None,
    delimiter: str = ",",
) -> str:
    """Export generic row dicts to a CSV string.

    Parameters
    ----------
    rows:
        Sequence of dicts; each dict becomes one CSV row.
    columns:
        Explicit column order.  If ``None`` keys of the first row are used.
    delimiter:
        Field separator character.
    """
    if not rows:
        return ""
    cols = list(columns) if columns else list(rows[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=cols,
        delimiter=delimiter,
        extrasaction="ignore",
    )
    csv.writer(buf, delimiter=delimiter).writerow([_safe_cell(column) for column in cols])
    for row in rows:
        safe = {k: _safe_cell(row.get(k, "")) for k in cols}
        writer.writerow(safe)
    return buf.getvalue()
