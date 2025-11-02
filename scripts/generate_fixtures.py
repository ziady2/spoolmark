"""Generate test fixture files."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def main() -> None:
    _gen_srt()
    _gen_vtt()
    _gen_ass()
    _gen_json()
    print(f"Fixtures written to {FIXTURES}")


def _gen_srt() -> None:
    text = """\
1
00:00:01,000 --> 00:00:04,000
Hello, world!

2
00:00:05,500 --> 00:00:08,200
This is a test subtitle file.

3
00:00:10,000 --> 00:00:13,500
Third cue with <i>italic</i> text.
"""
    (FIXTURES / "srt" / "sample.srt").write_text(text, encoding="utf-8")


def _gen_vtt() -> None:
    text = """\
WEBVTT

1
00:00:01.000 --> 00:00:04.000
Hello, world!

2
00:00:05.500 --> 00:00:08.200
This is a WebVTT file.

3
00:00:10.000 --> 00:00:13.500
Third cue.
"""
    (FIXTURES / "vtt" / "sample.vtt").write_text(text, encoding="utf-8")


def _gen_ass() -> None:
    text = """\
[Script Info]
Title: Test
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,Default,Speaker1,0,0,0,,Hello from ASS format!
Dialogue: 0,0:00:05.50,0:00:08.20,Default,Speaker2,0,0,0,,Second dialogue line.
"""
    (FIXTURES / "ass" / "sample.ass").write_text(text, encoding="utf-8")


def _gen_json() -> None:
    data = {
        "name": "JSON Track",
        "cues": [
            {"index": 1, "start": 1.0, "end": 4.0, "text": "Hello from JSON!"},
            {"index": 2, "start": 5.5, "end": 8.2, "text": "Second cue."},
            {"index": 3, "start": 10.0, "end": 13.5, "text": "Third cue."},
        ],
    }
    (FIXTURES / "json" / "sample.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
