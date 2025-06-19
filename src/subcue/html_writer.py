"""HTML subtitle preview renderer."""

from __future__ import annotations

from typing import Sequence

from .cue import Cue
from .text_utils import escape_html
from .track import Track

_DEFAULT_CSS = (
    "body{font-family:sans-serif;margin:2em;background:#fafafa}"
    "table{border-collapse:collapse;width:100%}"
    "th,td{border:1px solid #ccc;padding:6px 10px;text-align:left}"
    "th{background:#eee}"
    ".cue{margin:.4em 0;padding:.4em}"
    ".speaker{font-weight:bold;color:#336}"
)


def _tag(name: str, content: str, cls: str = "") -> str:
    """Wrap *content* in an HTML tag with optional class."""
    attr = f' class="{cls}"' if cls else ""
    return f"<{name}{attr}>{content}</{name}>"


def render_cue_list(
    cues: Sequence[Cue],
    *,
    show_index: bool = True,
    show_speaker: bool = True,
) -> str:
    """Render cues as styled HTML div elements.

    Parameters
    ----------
    cues:
        Sequence of *Cue* objects to render.
    show_index:
        Include the numeric index of each cue.
    show_speaker:
        Include the speaker label when present.
    """
    parts: list[str] = []
    for c in cues:
        idx_span = ""
        if show_index:
            idx_span = _tag("span", str(c.index), "idx") + " "
        speaker_span = ""
        if show_speaker and c.speaker:
            safe = escape_html(c.speaker)
            speaker_span = _tag("span", safe, "speaker") + ": "
        text = escape_html(c.text)
        parts.append(_tag("div", f"{idx_span}{speaker_span}{text}", "cue"))
    return "\n".join(parts)


def render_report_table(
    rows: Sequence[dict[str, object]],
    columns: Sequence[str] | None = None,
) -> str:
    """Build an HTML ``<table>`` from a list of row dicts.

    When *columns* is ``None`` the keys of the first row are used.
    """
    if not rows:
        return "<table><tr><td>No data</td></tr></table>"
    cols = list(columns) if columns else list(rows[0].keys())
    header = "".join(_tag("th", escape_html(str(c))) for c in cols)
    body_parts: list[str] = []
    for row in rows:
        cells = "".join(_tag("td", escape_html(str(row.get(c, "")))) for c in cols)
        body_parts.append(f"<tr>{cells}</tr>")
    body = "\n".join(body_parts)
    return f"<table>\n<tr>{header}</tr>\n{body}\n</table>"


def wrap_html_page(
    body: str,
    *,
    title: str = "Subcue Report",
    css: str = "",
) -> str:
    """Wrap *body* HTML in a complete HTML5 page with optional CSS."""
    style = css if css else _DEFAULT_CSS
    return "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            f"<title>{escape_html(title)}</title>",
            f"<style>{style}</style>",
            "</head>",
            "<body>",
            f"<h1>{escape_html(title)}</h1>",
            body,
            "</body>",
            "</html>",
        ]
    )


def render_track_preview(
    track: Track,
    *,
    max_cues: int = 200,
) -> str:
    """Build a full HTML page previewing a track's cues."""
    subset = track.cues[:max_cues]
    cue_html = render_cue_list(subset)
    name = escape_html(track.name or "untitled")
    lang = escape_html(track.language or "unknown")
    total = len(track.cues)
    info = f"<p>Track: <strong>{name}</strong> | Language: {lang} | Cues: {total}</p>"
    return wrap_html_page(
        info + "\n" + cue_html,
        title=f"Preview \u2013 {track.name or 'track'}",
    )
