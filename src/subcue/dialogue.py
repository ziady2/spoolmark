"""Dialogue helpers for speaker-attributed subtitles."""

from __future__ import annotations

from typing import Any, List

from .cue import Cue
from .speaker import Speaker, extract_speakers


class DialogueLine:
    """A cue explicitly tied to a speaker."""

    __slots__ = ("cue", "speaker")

    def __init__(self, cue: Cue, speaker: Speaker) -> None:
        self.cue = cue
        self.speaker = speaker

    def __repr__(self) -> str:
        return f"DialogueLine({self.speaker.name!r}, {self.cue.plain_text[:30]!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"speaker": self.speaker.to_dict(), "cue": self.cue.to_dict()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DialogueLine":
        return cls(Cue.from_dict(data["cue"]), Speaker.from_dict(data["speaker"]))


def build_dialogue(cues: list[Cue]) -> list[DialogueLine]:
    """Convert cues with speaker fields to DialogueLines."""
    speakers = {s.name.lower(): s for s in extract_speakers(cues)}
    lines: list[DialogueLine] = []
    for cue in cues:
        if cue.speaker:
            sp = speakers.get(cue.speaker.lower(), Speaker(cue.speaker))
            lines.append(DialogueLine(cue, sp))
    return lines


def speaker_turns(dialogue: list[DialogueLine]) -> List[dict]:
    """Count consecutive speaker turns."""
    if not dialogue:
        return []
    turns: List[dict] = []
    current = dialogue[0].speaker.name
    count = 1
    for dl in dialogue[1:]:
        if dl.speaker.name.lower() == current.lower():
            count += 1
        else:
            turns.append({"speaker": current, "cue_count": count})
            current = dl.speaker.name
            count = 1
    turns.append({"speaker": current, "cue_count": count})
    return turns


def dialogue_ratio(cues: list[Cue]) -> float:
    """Return fraction of cues that have a speaker attribution."""
    if not cues:
        return 0.0
    with_speaker = sum(1 for c in cues if c.speaker)
    return round(with_speaker / len(cues), 3)
