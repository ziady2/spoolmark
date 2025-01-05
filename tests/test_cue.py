"""Tests for cue."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.errors import ValidationError


class TestCue:
    def test_basic(self):
        c = Cue(1, 1.0, 4.0, "Hello")
        assert c.index == 1 and c.start == 1.0 and c.end == 4.0

    def test_duration(self):
        assert Cue(1, 1.0, 4.0, "Hi").duration == 3.0

    def test_mid(self):
        assert Cue(1, 1.0, 3.0, "Hi").mid == 2.0

    def test_cps(self):
        c = Cue(1, 0, 2.0, "Hello")
        assert c.cps > 0

    def test_plain_text(self):
        c = Cue(1, 0, 1, "<b>bold</b>")
        assert c.plain_text == "bold"

    def test_char_count(self):
        assert Cue(1, 0, 1, "hi").char_count == 2

    def test_word_count(self):
        assert Cue(1, 0, 1, "hello world").word_count == 2

    def test_negative_start_raises(self):
        with pytest.raises(ValidationError):
            Cue(1, -1, 1, "x")

    def test_end_before_start_raises(self):
        with pytest.raises(ValidationError):
            Cue(1, 5, 3, "x")

    @pytest.mark.parametrize(
        ("start", "end"),
        [
            (float("nan"), 1),
            (0, float("nan")),
            (float("inf"), float("inf")),
            (False, 1),
            (0, True),
        ],
    )
    def test_rejects_non_finite_and_boolean_timings(self, start, end):
        with pytest.raises(ValidationError):
            Cue(1, start, end, "x")

    def test_equality(self):
        assert Cue(1, 0, 1, "x") == Cue(2, 0, 1, "x")

    def test_hash(self):
        assert isinstance(hash(Cue(1, 0, 1, "x")), int)

    def test_to_dict(self):
        d = Cue(1, 1, 2, "hi").to_dict()
        assert d["index"] == 1 and d["text"] == "hi"

    def test_from_dict(self):
        c = Cue.from_dict({"index": 1, "start": 0, "end": 1, "text": "x"})
        assert c.text == "x"

    def test_copy(self):
        c = Cue(1, 0, 1, "x")
        cp = c.copy()
        assert cp == c and cp is not c

    def test_shift(self):
        c = Cue(1, 1, 3, "x").shift(2)
        assert c.start == 3 and c.end == 5

    def test_scale(self):
        c = Cue(1, 2, 4, "x").scale(2.0)
        assert c.start == 4 and c.end == 8

    def test_scale_zero_raises(self):
        with pytest.raises(ValidationError):
            Cue(1, 0, 1, "x").scale(0)

    @pytest.mark.parametrize("factor", [float("nan"), float("inf"), True])
    def test_scale_rejects_non_finite_or_boolean_factor(self, factor):
        with pytest.raises(ValidationError):
            Cue(1, 0, 1, "x").scale(factor)

    def test_overlaps(self):
        a = Cue(1, 0, 3, "x")
        b = Cue(2, 2, 5, "y")
        assert a.overlaps(b)

    def test_no_overlap(self):
        a = Cue(1, 0, 2, "x")
        b = Cue(2, 3, 5, "y")
        assert not a.overlaps(b)

    def test_gap_to(self):
        a = Cue(1, 0, 2, "x")
        b = Cue(2, 3, 5, "y")
        assert a.gap_to(b) == 1.0

    def test_with_text(self):
        c = Cue(1, 0, 1, "old").with_text("new")
        assert c.text == "new"

    def test_with_speaker(self):
        c = Cue(1, 0, 1, "hi").with_speaker("JOHN")
        assert c.speaker == "JOHN"

    def test_repr(self):
        assert "Cue" in repr(Cue(1, 0, 1, "x"))

    def test_lt(self):
        assert Cue(1, 0, 1, "x") < Cue(2, 1, 2, "y")
