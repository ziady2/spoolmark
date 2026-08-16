"""Text normalization utilities for subtitle content."""

from __future__ import annotations

import re
import unicodedata

from .track import Track

_OCR_I_RE = re.compile(r"(?<!\w)(?:l'll|l'm|l'd|lt's|lf|ln)(?!\w)|(?<![\w'])l(?![\w'])")
_OCR_I_REPLACEMENTS = {
    "l": "I",
    "l'm": "I'm",
    "l'd": "I'd",
    "l'll": "I'll",
    "lt's": "It's",
    "lf": "If",
    "ln": "In",
}


def normalize_unicode(text: str) -> str:
    """Apply NFC normalization to unify composed/decomposed characters."""
    return unicodedata.normalize("NFC", text)


def normalize_quotes(text: str) -> str:
    """Replace fancy quotes with straight quotes."""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00ab": '"',
        "\u00bb": '"',
        "\u2039": "'",
        "\u203a": "'",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def normalize_dashes(text: str) -> str:
    """Replace em/en dashes with hyphens."""
    return text.replace("\u2013", "-").replace("\u2014", "--")


def normalize_ellipsis(text: str) -> str:
    """Replace each ASCII three-dot sequence with a Unicode ellipsis."""
    return text.replace("...", "\u2026")


def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces and normalize line breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.splitlines():
        lines.append(re.sub(r"[ \t]+", " ", line).strip())
    return "\n".join(lines)


def strip_hearing_impaired(text: str) -> str:
    """Remove hearing-impaired annotations like [music] or (footsteps)."""
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"\([^)]*\)", "", text)
    return normalize_whitespace(text)


def strip_speaker_prefix(text: str) -> str:
    """Remove speaker prefixes like 'JOHN: Hello' -> 'Hello'."""
    return re.sub(r"^[A-Z][A-Z0-9 _.-]{0,30}:\s*", "", text, flags=re.MULTILINE)


def fix_common_ocr_errors(text: str) -> str:
    """Fix conservative, token-level OCR errors and punctuation spacing.

    OCR output commonly confuses an uppercase ``I`` with a lowercase ``l``.
    Only complete, known tokens are corrected so legitimate words ending in
    ``lf`` or ``ln`` are not changed.
    """
    punctuation_fixes = {
        " ,": ",",
        " .": ".",
        " !": "!",
        " ?": "?",
    }
    for old, new in punctuation_fixes.items():
        text = text.replace(old, new)
    return _OCR_I_RE.sub(lambda match: _OCR_I_REPLACEMENTS[match.group(0)], text)


def capitalize_sentences(text: str) -> str:
    """Capitalize the first letter of each sentence."""
    result = []
    for line in text.splitlines():
        sentences = re.split(r"([.!?]\s+)", line)
        processed = []
        for i, part in enumerate(sentences):
            if i % 2 == 0 and part:
                processed.append(part[0].upper() + part[1:])
            else:
                processed.append(part)
        result.append("".join(processed))
    return "\n".join(result)


def remove_duplicate_lines(text: str) -> str:
    """Remove consecutive duplicate lines."""
    lines = text.splitlines()
    result: list[str] = []
    for line in lines:
        if not result or line.strip() != result[-1].strip():
            result.append(line)
    return "\n".join(result)


def normalize_track(track: Track) -> Track:
    """Normalize cue text while preserving the track's metadata."""
    new_cues = []
    for cue in track.cues:
        text = normalize_cue_text(cue.text)
        text = remove_duplicate_lines(text)
        new_cues.append(cue.with_text(text))
    return Track(
        track.name,
        cues=new_cues,
        language=track.language,
        created=track.created,
    )


def normalize_cue_text(text: str) -> str:
    """Apply the safe typographic normalization pipeline to one string.

    Content-removing or interpretive helpers such as
    :func:`strip_hearing_impaired`, :func:`fix_common_ocr_errors`, and
    :func:`capitalize_sentences` remain explicit opt-in operations.
    """
    text = normalize_unicode(text)
    text = normalize_quotes(text)
    text = normalize_dashes(text)
    text = normalize_ellipsis(text)
    text = normalize_whitespace(text)
    return text
