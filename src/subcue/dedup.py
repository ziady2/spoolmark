"""Duplicate cue detection and removal."""

from __future__ import annotations

import math
from typing import Any, Sequence

from .cue import Cue


def _valid_fields() -> frozenset[str]:
    """Return public Cue data attributes that can safely form a key."""
    return frozenset(Cue.__slots__) | {
        "duration",
        "mid",
        "cps",
        "plain_text",
        "char_count",
        "word_count",
        "line_count",
    }


def _validated_fields(fields: Sequence[str]) -> tuple[str, ...]:
    """Return validated public Cue attributes used to build a key."""
    if isinstance(fields, (str, bytes)) or not isinstance(fields, Sequence):
        raise ValueError("fields must be a non-empty sequence of Cue attribute names")
    field_names = tuple(fields)
    if not field_names:
        raise ValueError("fields must be a non-empty sequence of Cue attribute names")
    allowed = _valid_fields()
    invalid = [field for field in field_names if not isinstance(field, str) or field not in allowed]
    if invalid:
        rendered = ", ".join(repr(field) for field in invalid)
        raise ValueError(f"unknown Cue field(s): {rendered}")
    return field_names


def _cue_key(cue: Cue, fields: Sequence[str]) -> tuple[Any, ...]:
    """Build a hashable key for a cue from the given *fields*."""
    return tuple(getattr(cue, field) for field in fields)


def find_duplicates(
    cues: Sequence[Cue],
    *,
    fields: Sequence[str] = ("start", "end", "text"),
    tolerance: float = 0.0,
) -> list[list[Cue]]:
    """Identify groups of duplicate cues.

    Two cues are considered duplicates when the specified *fields* match.
    For numeric timing fields, an absolute *tolerance* is applied.

    Parameters
    ----------
    cues:
        Cue objects to inspect.
    fields:
        Cue attribute names used for comparison.
    tolerance:
        Allowed difference for numeric comparisons (seconds).
    """
    if (
        isinstance(tolerance, bool)
        or not isinstance(tolerance, (int, float))
        or not math.isfinite(tolerance)
        or tolerance < 0
    ):
        raise ValueError("tolerance must be a finite non-negative number")
    field_names = _validated_fields(fields)
    groups: dict[tuple[Any, ...], list[Cue]] = {}
    for c in cues:
        key = _cue_key(c, field_names)
        placed = False
        if tolerance > 0:
            for existing_key, group in groups.items():
                match = True
                for k_part, e_part in zip(key, existing_key):
                    if isinstance(k_part, (int, float)) and isinstance(e_part, (int, float)):
                        if not math.isclose(
                            k_part,
                            e_part,
                            rel_tol=0.0,
                            abs_tol=tolerance + max(1e-12, tolerance * 1e-12),
                        ):
                            match = False
                            break
                    elif k_part != e_part:
                        match = False
                        break
                if match:
                    group.append(c)
                    placed = True
                    break
        if not placed:
            groups.setdefault(key, []).append(c)
    return [g for g in groups.values() if len(g) > 1]


def deduplicate(
    cues: Sequence[Cue],
    *,
    fields: Sequence[str] = ("start", "end", "text"),
) -> list[Cue]:
    """Return *cues* with duplicates removed, keeping the first occurrence.

    Uses the same field-matching logic as :func:`find_duplicates`.
    """
    field_names = _validated_fields(fields)
    seen: set[tuple[Any, ...]] = set()
    result: list[Cue] = []
    for c in cues:
        key = _cue_key(c, field_names)
        if key not in seen:
            seen.add(key)
            result.append(c)
    return result


def merge_duplicates(
    cues: Sequence[Cue],
    *,
    fields: Sequence[str] = ("start", "end", "text"),
    separator: str = " / ",
) -> list[Cue]:
    """Merge duplicate cues by combining their text.

    For each group of duplicates, the first cue is kept and the text
    of subsequent duplicates is appended with *separator*.

    Parameters
    ----------
    cues:
        Cue objects to process.
    fields:
        Fields defining duplicates.
    separator:
        String used to join duplicate texts.
    """
    field_names = _validated_fields(fields)
    groups: dict[tuple[Any, ...], list[Cue]] = {}
    order: list[tuple[Any, ...]] = []
    for c in cues:
        key = _cue_key(c, field_names)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(c)
    result: list[Cue] = []
    for key in order:
        group = groups[key]
        base = group[0].copy()
        if len(group) > 1:
            texts = [g.text for g in group]
            combined = separator.join(texts)
            object.__setattr__(base, "text", combined)
        result.append(base)
    return result
