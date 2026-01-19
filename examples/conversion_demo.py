"""Example: file and timecode conversion between SRT and WebVTT."""

from __future__ import annotations

from subcue.conversion import srt_to_vtt, vtt_to_srt
from subcue.io import parse_track, serialize_track
from subcue.srt_import import parse_srt_text
from subcue.vtt_import import cues_to_vtt

SAMPLE_SRT = """\
1
00:00:01,000 --> 00:00:04,000
Hello, world!

2
00:00:05,500 --> 00:00:08,200
Converting between formats.
"""


def main() -> None:
    # Whole-file conversion uses the high-level parse/serialise API.
    parsed = parse_track(SAMPLE_SRT, "srt", name="Conversion Demo")
    vtt_text = serialize_track(parsed, "vtt")
    print("=== SRT document to WebVTT ===")
    print(vtt_text)

    # The conversion helpers operate on one timecode, not a whole document.
    vtt_timecode = srt_to_vtt("00:01:23,456")
    print(f"Single timecode: {vtt_timecode} -> {vtt_to_srt(vtt_timecode)}")

    # Format-specific parsers and writers are useful for track manipulation.
    track = parse_srt_text(SAMPLE_SRT)
    print(f"Parsed {len(track)} cues")

    # Shift forward one second, then export the resulting cues.
    shifted = track.shift(1.0)
    vtt_output = cues_to_vtt(shifted.cues)
    print("\n=== Shifted VTT ===")
    print(vtt_output)


if __name__ == "__main__":
    main()
