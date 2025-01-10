"""Tests for dialogue."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.dialogue import build_dialogue, dialogue_ratio, speaker_turns


class TestBuildDialogue:
    def test_basic(self):
        cues = [Cue(1, 0, 1, "x", speaker="A"), Cue(2, 2, 3, "y", speaker="B")]
        dl = build_dialogue(cues)
        assert len(dl) == 2

    def test_no_speaker(self):
        cues = [Cue(1, 0, 1, "x")]
        assert build_dialogue(cues) == []


class TestSpeakerTurns:
    def test_basic(self):
        cues = [
            Cue(1, 0, 1, "x", speaker="A"),
            Cue(2, 2, 3, "y", speaker="A"),
            Cue(3, 4, 5, "z", speaker="B"),
        ]
        dl = build_dialogue(cues)
        turns = speaker_turns(dl)
        assert turns[0]["cue_count"] == 2


class TestDialogueRatio:
    def test_all_speakers(self):
        cues = [Cue(1, 0, 1, "x", speaker="A")]
        assert dialogue_ratio(cues) == 1.0

    def test_no_speakers(self):
        cues = [Cue(1, 0, 1, "x")]
        assert dialogue_ratio(cues) == 0.0

    def test_empty(self):
        assert dialogue_ratio([]) == 0.0
