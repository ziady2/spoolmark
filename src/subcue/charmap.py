"""Character mapping and encoding utilities for subtitle text."""

from __future__ import annotations

import re
from typing import Dict, List

# Common subtitle encoding issues and their fixes
_ENCODING_FIXES: Dict[str, str] = {
    "\u00e2\u0080\u0099": "\u2019",  # Right single quote
    "\u00e2\u0080\u009c": "\u201c",  # Left double quote
    "\u00e2\u0080\u009d": "\u201d",  # Right double quote
    "\u00e2\u0080\u0093": "\u2013",  # En dash
    "\u00e2\u0080\u0094": "\u2014",  # Em dash
    "\u00e2\u0080\u00a6": "\u2026",  # Ellipsis
    "\u00c3\u00a9": "\u00e9",  # e-acute (double encoding)
    "\u00c3\u00a8": "\u00e8",  # e-grave
    "\u00c3\u00b1": "\u00f1",  # n-tilde
}

# HTML entity map for subtitle use
_HTML_ENTITIES: Dict[str, str] = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&apos;": "'",
    "&nbsp;": " ",
    "&#39;": "'",
    "&#34;": '"',
}


def fix_encoding(text: str) -> str:
    """Fix common double-encoding artifacts in subtitle text."""
    for bad, good in _ENCODING_FIXES.items():
        text = text.replace(bad, good)
    return text


def decode_html_entities(text: str) -> str:
    """Replace HTML entities with their character equivalents."""
    for entity, char in _HTML_ENTITIES.items():
        text = text.replace(entity, char)
    # Numeric entities
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)
    return text


def detect_encoding_issues(text: str) -> List[dict]:
    """Detect potential encoding problems in text.

    Returns a list of dicts with ``position``, ``suspect``, ``suggestion``.
    """
    issues: List[dict] = []
    for bad, good in _ENCODING_FIXES.items():
        pos = text.find(bad)
        while pos >= 0:
            issues.append(
                {
                    "position": pos,
                    "suspect": repr(bad),
                    "suggestion": good,
                }
            )
            pos = text.find(bad, pos + 1)
    return issues


def transliterate_basic(text: str) -> str:
    """Basic transliteration of accented characters to ASCII."""
    import unicodedata

    nfkd = unicodedata.normalize("NFKD", text)
    return nfkd.encode("ascii", "ignore").decode("ascii")


def character_frequency(text: str) -> Dict[str, int]:
    """Count character frequencies (excluding spaces and newlines)."""
    freq: Dict[str, int] = {}
    for ch in text:
        if ch in (" ", "\n", "\r", "\t"):
            continue
        freq[ch] = freq.get(ch, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


def detect_script(text: str) -> str:
    """Detect the primary script used in text.

    Returns one of: 'latin', 'arabic', 'cjk', 'cyrillic', 'devanagari', 'other'.
    """
    scripts: Dict[str, int] = {
        "latin": 0,
        "arabic": 0,
        "cjk": 0,
        "cyrillic": 0,
        "devanagari": 0,
        "other": 0,
    }
    for ch in text:
        cp = ord(ch)
        if 0x0041 <= cp <= 0x024F:
            scripts["latin"] += 1
        elif 0x0600 <= cp <= 0x06FF:
            scripts["arabic"] += 1
        elif 0x4E00 <= cp <= 0x9FFF or 0x3040 <= cp <= 0x30FF:
            scripts["cjk"] += 1
        elif 0x0400 <= cp <= 0x04FF:
            scripts["cyrillic"] += 1
        elif 0x0900 <= cp <= 0x097F:
            scripts["devanagari"] += 1
        elif not ch.isspace():
            scripts["other"] += 1
    if not any(scripts.values()):
        return "other"
    return max(scripts, key=scripts.get)  # type: ignore[arg-type]


def is_rtl(text: str) -> bool:
    """Check if text is primarily right-to-left."""
    script = detect_script(text)
    return script in ("arabic",)


def clean_subtitle_text(text: str) -> str:
    """Apply all cleaning steps to subtitle text."""
    text = fix_encoding(text)
    text = decode_html_entities(text)
    return text
