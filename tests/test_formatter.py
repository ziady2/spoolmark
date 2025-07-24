"""Tests for formatter."""

from __future__ import annotations

from subcue.formatter import (
    format_cps,
    format_duration,
    format_filesize,
    format_number,
    format_percentage,
    format_timecode_display,
)


class Test_format_cps:
    def test_callable(self):
        assert callable(format_cps)


class Test_format_duration:
    def test_callable(self):
        assert callable(format_duration)


class Test_format_filesize:
    def test_callable(self):
        assert callable(format_filesize)


class Test_format_number:
    def test_callable(self):
        assert callable(format_number)


class Test_format_percentage:
    def test_callable(self):
        assert callable(format_percentage)


class Test_format_timecode_display:
    def test_callable(self):
        assert callable(format_timecode_display)

    def test_rounding_carries_into_next_minute(self):
        assert format_timecode_display(59.9996) == "00:01:00.000"
        assert ":60." not in format_timecode_display(3599.9996)
