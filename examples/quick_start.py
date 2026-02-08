"""Quick-start example: parse SRT and analyse CPS."""

from __future__ import annotations

from subcue.report_cps import cps_per_cue
from subcue.srt_import import parse_srt_text

SAMPLE_SRT = """\
1
00:00:01,000 --> 00:00:04,000
Hello and welcome to this video.

2
00:00:05,500 --> 00:00:07,500
Today we will talk about subtitles.

3
00:00:08,000 --> 00:00:09,000
They are important for accessibility.

4
00:00:10,000 --> 00:00:14,000
Let us look at some examples of good and bad timing.
"""


def main() -> None:
    track = parse_srt_text(SAMPLE_SRT)
    print(f"Parsed {len(track)} cues\n")

    rows = cps_per_cue(track)
    for row in rows:
        print(
            f"  Cue {row['index']:>2}: CPS={row['cps']:>5.1f}  "
            f"{row['rating']:<6}  {row['text_preview']}"
        )


if __name__ == "__main__":
    main()
