"""Tests for conversion."""

from __future__ import annotations

from subcue.conversion import (
    batch_convert_srt_to_vtt,
    batch_convert_vtt_to_srt,
    format_timecode,
    format_timecode_vtt,
    fps_factor,
    framerate_convert,
    parse_timecode,
    srt_to_vtt,
)


class Test_batch_convert_srt_to_vtt:
    def test_callable(self):
        assert callable(batch_convert_srt_to_vtt)


class Test_batch_convert_vtt_to_srt:
    def test_callable(self):
        assert callable(batch_convert_vtt_to_srt)


class Test_format_timecode:
    def test_callable(self):
        assert callable(format_timecode)


class Test_format_timecode_vtt:
    def test_callable(self):
        assert callable(format_timecode_vtt)


class Test_fps_factor:
    def test_callable(self):
        assert callable(fps_factor)


class Test_framerate_convert:
    def test_callable(self):
        assert callable(framerate_convert)


class Test_parse_timecode:
    def test_callable(self):
        assert callable(parse_timecode)


class Test_srt_to_vtt:
    def test_callable(self):
        assert callable(srt_to_vtt)
