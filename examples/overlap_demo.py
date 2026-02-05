"""Example: detect overlapping cues."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.track import Track


def main() -> None:
    cues = [
        Cue(1, 0.0, 3.0, "First cue"),
        Cue(2, 2.5, 5.0, "Overlaps with first!"),
        Cue(3, 6.0, 8.0, "No overlap"),
        Cue(4, 7.5, 10.0, "Overlaps with third"),
    ]
    track = Track("Test", cues=cues)

    pairs = track.overlapping_pairs()
    if pairs:
        print(f"Found {len(pairs)} overlapping pair(s):")
        for a, b in pairs:
            gap = round(a.end - b.start, 3)
            print(f"  Cue {a.index} and {b.index}: overlap {abs(gap):.3f}s")
    else:
        print("No overlaps found.")


if __name__ == "__main__":
    main()
