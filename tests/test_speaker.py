"""Tests for speaker."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.errors import ValidationError
from subcue.speaker import Speaker, extract_speakers


class TestSpeaker:
    def test_basic(self):
        s = Speaker("John")
        assert s.name == "John"

    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            Speaker("")

    def test_equality(self):
        assert Speaker("John") == Speaker("john")

    def test_to_dict(self):
        d = Speaker("X").to_dict()
        assert d["name"] == "X"

    def test_from_dict(self):
        s = Speaker.from_dict({"name": "Y"})
        assert s.name == "Y"

    def test_display(self):
        s = Speaker("John", language="en")
        assert "John" in s.display() and "en" in s.display()


class TestExtractSpeakers:
    def test_basic(self):
        cues = [Cue(1, 0, 1, "x", speaker="A"), Cue(2, 2, 3, "y", speaker="B")]
        speakers = extract_speakers(cues)
        assert len(speakers) == 2

    def test_empty(self):
        assert extract_speakers([]) == []

    def test_dedup(self):
        cues = [Cue(1, 0, 1, "x", speaker="A"), Cue(2, 2, 3, "y", speaker="A")]
        assert len(extract_speakers(cues)) == 1
