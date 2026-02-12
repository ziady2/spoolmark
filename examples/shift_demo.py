"""Example: shift subtitle timecodes."""

from __future__ import annotations

from subcue.srt_import import cues_to_srt, parse_srt_text

SAMPLE = """\
1
00:00:01,000 --> 00:00:03,000
First subtitle.

2
00:00:05,000 --> 00:00:08,000
Second subtitle.
"""


def main() -> None:
    track = parse_srt_text(SAMPLE)
    print("Original:")
    print(cues_to_srt(track.cues))

    shifted = track.shift(2.5)
    print("Shifted +2.5s:")
    print(cues_to_srt(shifted.cues))


if __name__ == "__main__":
    main()
