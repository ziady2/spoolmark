"""Example: speaker analysis for speaker-attributed cues."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.dialogue import build_dialogue, dialogue_ratio, speaker_turns
from subcue.track import Track


def main() -> None:
    cues = [
        Cue(1, 0.0, 2.0, "Hello everyone.", speaker="NARRATOR"),
        Cue(2, 2.5, 4.0, "Welcome to the show.", speaker="NARRATOR"),
        Cue(3, 5.0, 7.0, "Thanks for having me.", speaker="GUEST"),
        Cue(4, 7.5, 9.0, "Let's get started.", speaker="NARRATOR"),
        Cue(5, 10.0, 12.0, "Sure thing.", speaker="GUEST"),
    ]
    track = Track("Interview", cues=cues)
    dialogue = build_dialogue(track.cues)

    print(f"Dialogue ratio: {dialogue_ratio(track.cues):.0%}")
    print("\nSpeaker turns:")
    for turn in speaker_turns(dialogue):
        print(f"  {turn['speaker']}: {turn['cue_count']} cue(s)")


if __name__ == "__main__":
    main()
