"""Tests for marker."""

from __future__ import annotations

import json

import pytest

from subcue.errors import ValidationError
from subcue.marker import Marker, auto_chapter_markers, markers_in_range


class TestMarker:
    def test_basic(self):
        m = Marker(10.0, "Chapter 1")
        assert m.time == 10.0 and m.label == "Chapter 1"

    def test_negative_time_raises(self):
        with pytest.raises(ValidationError):
            Marker(-1, "Bad")

    @pytest.mark.parametrize(
        "time", [True, float("nan"), float("inf"), float("-inf"), "1", 10**1000]
    )
    def test_rejects_non_finite_or_non_numeric_times(self, time):
        with pytest.raises(ValidationError, match="finite"):
            Marker(time, "Bad")  # type: ignore[arg-type]

    def test_empty_label_raises(self):
        with pytest.raises(ValidationError):
            Marker(0, "")

    def test_equality(self):
        assert Marker(10, "A") == Marker(10, "A")

    def test_lt(self):
        assert Marker(1, "A") < Marker(2, "B")

    def test_shift(self):
        m = Marker(10, "X").shift(5)
        assert m.time == 15

    def test_to_dict(self):
        d = Marker(10, "X").to_dict()
        assert d["time"] == 10

    def test_to_dict_is_strict_json_compatible(self):
        payload = Marker(10, "X").to_dict()

        assert json.loads(json.dumps(payload, allow_nan=False))["time"] == 10

    @pytest.mark.parametrize("time", ["not-a-number", None, 10**1000])
    def test_from_dict_wraps_invalid_times_in_domain_error(self, time):
        with pytest.raises(ValidationError, match="time"):
            Marker.from_dict({"time": time, "label": "Bad"})

    @pytest.mark.parametrize("offset", [True, float("nan"), float("inf"), float("-inf"), 10**1000])
    def test_shift_rejects_non_finite_offsets(self, offset):
        with pytest.raises(ValidationError, match="offset"):
            Marker(10, "X").shift(offset)


class TestMarkersInRange:
    def test_basic(self):
        markers = [Marker(5, "A"), Marker(15, "B"), Marker(25, "C")]
        result = markers_in_range(markers, 10, 20)
        assert len(result) == 1


class TestAutoChapterMarkers:
    def test_basic(self):
        from subcue.cue import Cue

        cues = [Cue(1, 0, 300, "x"), Cue(2, 300, 600, "y")]
        markers = auto_chapter_markers(cues, interval=300)
        assert len(markers) >= 2

    @pytest.mark.parametrize(
        "interval",
        [0, -1, True, float("nan"), float("inf"), float("-inf"), "300", 10**1000],
    )
    def test_rejects_non_positive_interval(self, interval):
        with pytest.raises(ValidationError):
            auto_chapter_markers([], interval=interval)  # type: ignore[arg-type]
