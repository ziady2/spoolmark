"""Accessibility helpers for rendered subtitle output."""

from __future__ import annotations

from typing import Any


def aria_label(element_type: str, description: str) -> str:
    """Generate an aria-label attribute value."""
    return f"{element_type}: {description}"


def alt_text_for_chart(chart_type: str, data_summary: str, *, title: str = "") -> str:
    """Generate descriptive alt text for a chart image."""
    parts = []
    if title:
        parts.append(f"{title}.")
    parts.append(f"{chart_type} chart showing {data_summary}.")
    return " ".join(parts)


def screen_reader_table(rows: list[dict], *, title: str = "", summary: str = "") -> str:
    """Screen-reader-friendly text representation of table data."""
    if not rows:
        return f"Empty table{': ' + title if title else ''}."
    cols = list(rows[0].keys())
    lines = []
    if title:
        lines.append(f"Table: {title}")
    if summary:
        lines.append(f"Summary: {summary}")
    lines.append(f"Columns: {', '.join(cols)}")
    lines.append(f"Rows: {len(rows)}")
    for i, row in enumerate(rows, 1):
        parts = [f"{c}={row.get(c, '')}" for c in cols]
        lines.append(f"  Row {i}: {', '.join(parts)}")
    return "\n".join(lines)


def screen_reader_cue(cue: Any) -> str:
    """Accessible text representation of a cue."""
    from .timing import format_timecode_vtt

    parts = [
        f"Cue {cue.index}.",
        f"From {format_timecode_vtt(cue.start)} to {format_timecode_vtt(cue.end)}.",
        f"Duration {cue.duration:.1f} seconds.",
    ]
    if cue.speaker:
        parts.append(f"Speaker: {cue.speaker}.")
    parts.append(f"Text: {cue.plain_text}")
    return " ".join(parts)


def contrast_check(fg_hex: str, bg_hex: str) -> dict[str, Any]:
    """Check WCAG contrast ratio between foreground and background colours."""
    fg_lum = _luminance(fg_hex)
    bg_lum = _luminance(bg_hex)
    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)
    ratio = round((lighter + 0.05) / (darker + 0.05), 2)
    return {
        "ratio": ratio,
        "aa_normal": ratio >= 4.5,
        "aa_large": ratio >= 3.0,
        "aaa_normal": ratio >= 7.0,
    }


def focus_order(elements: list[dict]) -> list[dict]:
    """Sort interactive elements into logical focus order."""
    return sorted(
        elements,
        key=lambda e: (
            e.get("position", {}).get("y", 0),
            e.get("position", {}).get("x", 0),
        ),
    )


def heading_hierarchy(headings: list[tuple[int, str]]) -> list[dict]:
    """Validate heading hierarchy (h1, h2, h3...)."""
    results: list[dict] = []
    prev = 0
    for level, text in headings:
        results.append({"level": level, "text": text, "valid": level <= prev + 1})
        prev = level
    return results


def simplify_text(text: str) -> str:
    """Simplify text for screen readers by removing decorative chars."""
    replacements = {
        "\u2502": "|",
        "\u2500": "-",
        "\u250c": "+",
        "\u2510": "+",
        "\u2514": "+",
        "\u2518": "+",
        "\u2550": "=",
        "\u2588": "#",
        "\u2591": ".",
        "\u2592": ".",
        "\u2593": "#",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return 0.0
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
