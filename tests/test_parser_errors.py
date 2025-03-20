"""Cross-format parser error contract tests."""

from __future__ import annotations

import pytest

from subcue.ass_import import parse_ass_text
from subcue.errors import ParseError
from subcue.srt_import import parse_srt_text
from subcue.txt_import import parse_txt_text
from subcue.vtt_import import parse_vtt_text


@pytest.mark.parametrize(
    ("parser", "source"),
    [
        (parse_srt_text, "1\n00:00:02,000 --> 00:00:01,000\nx"),
        (parse_vtt_text, "WEBVTT\n\n00:02.000 --> 00:01.000\nx"),
        (
            parse_ass_text,
            "[Events]\nDialogue: 0,0:00:02.00,0:00:01.00,Default,,0,0,0,,x",
        ),
        (parse_txt_text, "00:00:02.000 --> 00:00:01.000 | x"),
    ],
)
def test_reversed_timing_is_always_a_parse_error(parser, source: str) -> None:
    with pytest.raises(ParseError):
        parser(source)
