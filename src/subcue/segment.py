"""Subtitle segmentation -- break long text into timed cues."""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from .cue import Cue
from .track import Track
from .wordwrap import (
    _balance_html_fragments,
    _html_tag_end,
    _markup_words,
    _strict_partition,
    _visible_length,
    _visible_text,
    check_line_lengths,
)


def segment_text(
    text: str,
    start: float,
    end: float,
    *,
    max_chars_per_line: int = 42,
    max_lines: int = 2,
    min_duration: float = 0.7,
) -> List[Cue]:
    """Split a text block into display-ready, contiguous timed cues.

    Sentence boundaries are preferred, then whole-word boundaries.  HTML and
    ASS blocks count as zero-width markup and are never split.  Each cue
    respects ``max_chars_per_line`` and ``max_lines`` whenever whole words make
    that possible.  A single word longer than the width is emitted intact in
    its own cue, which is the one explicit width-overflow case.

    Every cue receives at least ``min_duration`` seconds.  If the requested
    interval cannot provide that minimum for all required cues, ``ValueError``
    is raised instead of silently creating invalid timings.
    """
    _validate_segment_arguments(
        text,
        start,
        end,
        max_chars_per_line=max_chars_per_line,
        max_lines=max_lines,
        min_duration=min_duration,
    )

    sentences = _split_sentences(text)
    if not sentences:
        return []

    raw_chunks = [
        chunk
        for sentence in sentences
        for chunk in _split_to_chunks(sentence, max_chars_per_line, max_lines)
    ]
    chunks = _balance_chunk_markup(raw_chunks)
    weights = [max(1, _visible_length(chunk.replace("\n", " "))) for chunk in chunks]
    total_weight = sum(weights)
    duration = float(end - start)
    minimum_total = len(chunks) * float(min_duration)
    if minimum_total > duration + 1e-12:
        raise ValueError(
            f"{len(chunks)} cues cannot each fit the {min_duration:g}s minimum "
            f"inside a {duration:g}s range"
        )

    remaining_duration = max(0.0, duration - minimum_total)
    cues: List[Cue] = []
    current_time = float(start)
    for position, (chunk, weight) in enumerate(zip(chunks, weights)):
        proportional = remaining_duration * weight / total_weight
        chunk_duration = float(min_duration) + proportional
        chunk_end = float(end) if position == len(chunks) - 1 else current_time + chunk_duration
        cues.append(Cue(len(cues) + 1, current_time, chunk_end, chunk))
        current_time = chunk_end
    return cues


def auto_segment_track(
    track: Track,
    *,
    max_chars_per_line: int = 42,
    max_lines: int = 2,
    min_duration: float = 0.7,
) -> Track:
    """Re-segment nonconforming cues while retaining track/cue metadata."""
    _validate_display_limits(max_chars_per_line, max_lines)
    _validate_min_duration(min_duration)
    if not isinstance(track, Track):
        raise TypeError("track must be a Track")

    new_cues: List[Cue] = []
    for cue in track.cues:
        report = check_line_lengths(
            cue.text,
            max_width=max_chars_per_line,
            max_lines=max_lines,
        )
        if report["conformant"]:
            new_cues.append(
                Cue(
                    len(new_cues) + 1,
                    cue.start,
                    cue.end,
                    cue.text,
                    speaker=cue.speaker,
                    style=cue.style,
                )
            )
            continue

        segments = segment_text(
            cue.text,
            cue.start,
            cue.end,
            max_chars_per_line=max_chars_per_line,
            max_lines=max_lines,
            min_duration=min_duration,
        )
        for segment in segments:
            new_cues.append(
                Cue(
                    len(new_cues) + 1,
                    segment.start,
                    segment.end,
                    segment.text,
                    speaker=cue.speaker,
                    style=cue.style,
                )
            )

    return Track(
        track.name,
        cues=new_cues,
        language=track.language,
        created=track.created,
    )


def estimate_cue_count(text: str, max_chars: int = 84) -> int:
    """Estimate cue count from visible characters, excluding markup."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if isinstance(max_chars, bool) or not isinstance(max_chars, int) or max_chars <= 0:
        raise ValueError("max_chars must be a positive integer")
    visible = " ".join(_visible_text(text).split())
    if not visible:
        return 0
    return max(1, (len(visible) + max_chars - 1) // max_chars)


def optimal_break_points(text: str, max_width: int = 42) -> List[int]:
    """Return safe raw-string indices for suggested line breaks.

    Width is measured on displayed text, while returned indices refer to the
    original tagged string.  Sentence punctuation is preferred, then commas,
    then whitespace.  If a token itself is too long, the next whole-word
    boundary is used even though it exceeds ``max_width``; a trailing overlong
    token has no break point.  An index is never inside an HTML or ASS block.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if isinstance(max_width, bool) or not isinstance(max_width, int) or max_width <= 0:
        raise ValueError("max_width must be a positive integer")

    visible, raw_after = _visible_text_map(text)
    if len(visible) <= max_width:
        return []

    boundaries = _break_boundaries(visible)
    breaks: List[int] = []
    visible_start = 0
    while len(visible) - visible_start > max_width:
        lower = visible_start + max(1, max_width // 2)
        upper = visible_start + max_width
        candidates = [
            boundary
            for boundary in boundaries
            if lower <= boundary[0] <= upper and boundary[0] < len(visible)
        ]
        chosen = _preferred_boundary(candidates)
        if chosen is None:
            later = [
                boundary
                for boundary in boundaries
                if boundary[0] > upper and boundary[0] < len(visible)
            ]
            if not later:
                break
            chosen = min(later, key=lambda boundary: boundary[0])
        visible_position = chosen[0]
        raw_position = raw_after[visible_position - 1]
        if not breaks or raw_position > breaks[-1]:
            breaks.append(raw_position)
        visible_start = visible_position
    return breaks


def _validate_segment_arguments(
    text: str,
    start: float,
    end: float,
    *,
    max_chars_per_line: int,
    max_lines: int,
    min_duration: float,
) -> None:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if isinstance(start, bool) or not isinstance(start, (int, float)):
        raise ValueError("start must be a finite non-negative number")
    if isinstance(end, bool) or not isinstance(end, (int, float)):
        raise ValueError("end must be a finite number greater than start")
    if not math.isfinite(start) or start < 0:
        raise ValueError("start must be a finite non-negative number")
    if not math.isfinite(end) or end <= start:
        raise ValueError("end must be a finite number greater than start")
    _validate_display_limits(max_chars_per_line, max_lines)
    _validate_min_duration(min_duration)


def _validate_display_limits(max_chars_per_line: int, max_lines: int) -> None:
    if (
        isinstance(max_chars_per_line, bool)
        or not isinstance(max_chars_per_line, int)
        or max_chars_per_line <= 0
    ):
        raise ValueError("max_chars_per_line must be a positive integer")
    if isinstance(max_lines, bool) or not isinstance(max_lines, int) or max_lines <= 0:
        raise ValueError("max_lines must be a positive integer")


def _validate_min_duration(min_duration: float) -> None:
    if (
        isinstance(min_duration, bool)
        or not isinstance(min_duration, (int, float))
        or not math.isfinite(min_duration)
        or min_duration < 0
    ):
        raise ValueError("min_duration must be a finite non-negative number")


def _split_sentences(text: str) -> List[str]:
    """Split after sentence punctuation without looking inside tags."""
    words = _markup_words(text.strip())
    sentences: List[str] = []
    current: List[str] = []
    for word in words:
        current.append(word)
        visible = _visible_text(word).rstrip()
        if visible.endswith((".", "!", "?")):
            sentences.append(" ".join(current))
            current = []
    if current:
        sentences.append(" ".join(current))
    return sentences


def _split_to_chunks(text: str, max_chars_per_line: int, max_lines: int) -> List[str]:
    """Split a sentence into the largest strictly conforming word groups."""
    _validate_display_limits(max_chars_per_line, max_lines)
    words = _markup_words(text)
    if not words:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(words):
        best_end: Optional[int] = None
        best_lines: Optional[List[str]] = None
        for end in range(start + 1, len(words) + 1):
            lines = _strict_partition(words[start:end], max_chars_per_line, max_lines)
            if lines is None:
                break
            best_end = end
            best_lines = lines

        if best_end is None or best_lines is None:
            # The first word itself is wider than the line.  Keeping it whole
            # in an otherwise isolated cue is the documented impossible case.
            chunks.append(words[start])
            start += 1
        else:
            chunks.append("\n".join(best_lines))
            start = best_end
    return chunks


def _balance_chunk_markup(chunks: Sequence[str]) -> List[str]:
    """Balance HTML independently at every line and cue boundary."""
    line_counts: List[int] = []
    flattened: List[str] = []
    for chunk in chunks:
        lines = chunk.split("\n")
        line_counts.append(len(lines))
        flattened.extend(lines)

    balanced_lines = _balance_html_fragments(flattened)
    balanced_chunks: List[str] = []
    position = 0
    for line_count in line_counts:
        balanced_chunks.append("\n".join(balanced_lines[position : position + line_count]))
        position += line_count
    return balanced_chunks


def _visible_text_map(text: str) -> Tuple[str, List[int]]:
    """Return tag-free text plus each visible character's raw end index."""
    visible: List[str] = []
    raw_after: List[int] = []
    position = 0
    while position < len(text):
        if text[position] == "<":
            end = _html_tag_end(text, position)
            if end is not None:
                position = end
                continue
        if text[position] == "{":
            closing = text.find("}", position + 1)
            if closing >= 0:
                position = closing + 1
                continue
        visible.append(text[position])
        raw_after.append(position + 1)
        position += 1
    return "".join(visible), raw_after


def _break_boundaries(visible: str) -> List[Tuple[int, str]]:
    boundaries: List[Tuple[int, str]] = []
    for position, character in enumerate(visible, 1):
        next_is_space = position == len(visible) or visible[position].isspace()
        if character in ".!?" and next_is_space:
            boundaries.append((position, "sentence"))
        elif character == "," and next_is_space:
            boundaries.append((position, "comma"))
        elif character.isspace():
            boundaries.append((position, "space"))
    return boundaries


def _preferred_boundary(boundaries: Sequence[Tuple[int, str]]) -> Optional[Tuple[int, str]]:
    for kind in ("sentence", "comma", "space"):
        matching = [boundary for boundary in boundaries if boundary[1] == kind]
        if matching:
            return max(matching, key=lambda boundary: boundary[0])
    return None
