"""Tests for timing."""

from __future__ import annotations

import pytest

from subcue.errors import TimecodeError
from subcue.timing import (
    cps,
    duration_between,
    format_duration_human,
    format_timecode,
    format_timecode_ass,
    format_timecode_vtt,
    gap,
    ms_to_timecode,
    overlap,
    parse_timecode,
    scale_time,
    shift_time,
    snap_to_frame,
    timecode_to_ms,
    wps,
)


class TestParseTimecode:
    def test_srt_format(self):
        assert abs(parse_timecode("00:01:23,456") - 83.456) < 0.001

    def test_vtt_format(self):
        assert abs(parse_timecode("00:01:23.456") - 83.456) < 0.001

    def test_short_format(self):
        assert abs(parse_timecode("1:23.456") - 83.456) < 0.001

    def test_plain_seconds(self):
        assert parse_timecode("10.5") == 10.5

    def test_bad_format(self):
        with pytest.raises(TimecodeError):
            parse_timecode("not-a-time")

    def test_zero(self):
        assert parse_timecode("00:00:00,000") == 0.0

    @pytest.mark.parametrize(
        "raw",
        [
            "00:00:01,000garbage",
            "00:60:00,000",
            "00:00:60,000",
            "nan",
            "inf",
            "-1",
        ],
    )
    def test_rejects_partial_non_finite_and_out_of_range_values(self, raw):
        with pytest.raises(TimecodeError):
            parse_timecode(raw)


class TestFormatTimecode:
    def test_basic(self):
        assert format_timecode(83.456) == "00:01:23,456"

    def test_zero(self):
        assert format_timecode(0) == "00:00:00,000"

    def test_negative(self):
        assert format_timecode(-1) == "00:00:00,000"

    def test_vtt(self):
        assert format_timecode_vtt(83.456) == "00:01:23.456"

    def test_ass(self):
        result = format_timecode_ass(83.45)
        assert "1:23" in result

    @pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
    def test_rejects_non_finite_or_boolean_values(self, value):
        with pytest.raises(ValueError, match="finite"):
            format_timecode(value)


class TestTimecodeConversions:
    def test_to_ms(self):
        assert timecode_to_ms(1.5) == 1500

    def test_ms_to_tc(self):
        assert ms_to_timecode(1500) == 1.5

    def test_duration_between(self):
        assert duration_between(1.0, 3.0) == 2.0


class TestShiftScale:
    def test_shift(self):
        assert shift_time(5.0, 2.0) == 7.0

    def test_shift_negative(self):
        assert shift_time(1.0, -5.0) == 0.0

    def test_scale(self):
        assert abs(scale_time(10.0, 1.5) - 15.0) < 0.001


class TestOverlapGap:
    def test_overlap(self):
        assert overlap(0, 3, 2, 5) == 1.0

    def test_no_overlap(self):
        assert overlap(0, 2, 3, 5) == 0.0

    def test_gap(self):
        assert gap(2.0, 3.0) == 1.0

    def test_negative_gap(self):
        assert gap(3.0, 2.0) == -1.0


class TestSnapToFrame:
    def test_24fps(self):
        result = snap_to_frame(1.0, 24.0)
        assert abs(result - 1.0) < 0.05


class TestCpsWps:
    def test_cps(self):
        assert cps("Hello world", 2.0) == 5.5

    def test_cps_zero_duration(self):
        assert cps("text", 0.0) == 0.0

    def test_wps(self):
        assert wps("Hello world here", 3.0) == 1.0


class TestFormatDurationHuman:
    @pytest.mark.parametrize(
        "secs,expected",
        [
            (30, "30s"),
            (90, "1m 30s"),
            (3600, "1h 0m 0s"),
            (0, "0s"),
        ],
    )
    def test_basic(self, secs, expected):
        assert format_duration_human(secs) == expected
