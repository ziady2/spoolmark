"""Tests for timeline."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.timeline import (
    align_to_keyframes,
    compress_timeline,
    find_silence_periods,
    stretch_to_fill,
    timeline_coverage,
    timeline_density,
    timeline_gaps,
)
from subcue.track import Track


def _track():
    return Track("T", cues=[Cue(1, 0, 2, "A"), Cue(2, 5, 7, "B"), Cue(3, 10, 12, "C")])


class TestTimelineCoverage:
    def test_basic(self):
        c = timeline_coverage(_track())
        assert 0 < c < 1

    def test_empty(self):
        assert timeline_coverage(Track("E")) == 0.0

    def test_counts_overlapping_time_only_once(self):
        track = Track(
            "T",
            cues=[
                Cue(1, 0, 10, "long"),
                Cue(2, 2, 3, "nested"),
                Cue(3, 12, 14, "later"),
            ],
        )
        assert timeline_coverage(track) == pytest.approx(12 / 14, abs=0.001)


class TestTimelineGaps:
    def test_basic(self):
        gaps = timeline_gaps(_track())
        assert len(gaps) == 2

    def test_empty(self):
        assert timeline_gaps(Track("E")) == []

    def test_nested_overlap_does_not_create_false_gap(self):
        track = Track(
            "T",
            cues=[
                Cue(1, 0, 10, "long"),
                Cue(2, 2, 3, "nested"),
                Cue(3, 12, 13, "next"),
            ],
        )
        assert timeline_gaps(track) == [{"start": 10, "end": 12, "duration": 2}]


class TestTimelineDensity:
    def test_basic(self):
        rows = timeline_density(_track(), interval=5.0)
        assert len(rows) > 0

    def test_empty(self):
        assert timeline_density(Track("E")) == []

    def test_uses_latest_end_even_when_last_starting_cue_ends_earlier(self):
        track = Track("T", cues=[Cue(1, 0, 20, "long"), Cue(2, 10, 11, "nested")])
        rows = timeline_density(track, interval=5.0)
        assert len(rows) == 4
        assert rows[-1]["interval_end"] == 20.0

    def test_late_first_cue_does_not_create_empty_leading_windows(self):
        track = Track("late", cues=[Cue(1, 1_000_000, 1_000_001, "late")])
        rows = timeline_density(track, interval=0.5)
        assert len(rows) == 2
        assert rows[0]["cue_count"] == 1

    @pytest.mark.parametrize("interval", [0, -1])
    def test_rejects_non_positive_interval(self, interval):
        with pytest.raises(ValueError):
            timeline_density(_track(), interval=interval)

    @pytest.mark.parametrize("interval", [float("nan"), float("inf"), True])
    def test_rejects_non_finite_or_boolean_interval(self, interval):
        with pytest.raises(ValueError, match="finite"):
            timeline_density(_track(), interval=interval)

    def test_preserves_sub_tenth_bin_boundaries(self):
        track = Track("fine", cues=[Cue(1, 0, 0.12, "x")])
        rows = timeline_density(track, interval=0.04)

        assert len(rows) == 3
        assert [row["interval_start"] for row in rows] == pytest.approx([0, 0.04, 0.08])
        assert [row["interval_end"] for row in rows] == pytest.approx([0.04, 0.08, 0.12])
        assert all(row["interval_end"] > row["interval_start"] for row in rows)

    def test_rejects_interval_that_cannot_advance_at_large_timestamps(self):
        track = Track("large", cues=[Cue(1, 1e16, 1e16 + 2, "x")])

        with pytest.raises(ValueError, match="too small to advance"):
            timeline_density(track, interval=0.1)


class TestFindSilence:
    def test_basic(self):
        periods = find_silence_periods(_track(), min_silence=2.0)
        assert len(periods) >= 1


class TestCompressTimeline:
    def test_basic(self):
        result = compress_timeline(_track())
        assert len(result) == 3
        gaps = timeline_gaps(result)
        assert all(g["duration"] < 0.1 for g in gaps)

    def test_false_flag_returns_an_unchanged_deep_copy(self):
        original = Track("T", cues=[Cue(1, 2, 3, "x")], created="today")
        result = compress_timeline(original, remove_gaps=False)
        assert result.to_dict() == original.to_dict()
        assert result is not original
        assert result[0] is not original[0]

    def test_preserves_created_metadata(self):
        original = Track("T", cues=[Cue(1, 2, 3, "x")], created="today")
        assert compress_timeline(original).created == "today"

    def test_preserves_sub_millisecond_duration_without_rounding(self):
        original = Track("T", cues=[Cue(1, 0, 0.0004, "tiny")])
        result = compress_timeline(original)

        assert result[0].end - result[0].start == pytest.approx(0.0004, abs=1e-15)
        assert result[0].text == "tiny"


class TestStretchToFill:
    def test_basic(self):
        result = stretch_to_fill(_track(), target_duration=24.0)
        assert abs(result.duration - 24.0) < 1.0

    def test_uses_raw_span_for_sub_millisecond_track(self):
        track = Track("tiny", cues=[Cue(1, 0, 0.0004, "x")])
        result = stretch_to_fill(track, target_duration=1.0)

        assert result[0].end - result[0].start == pytest.approx(1.0)
        assert track[0].end == 0.0004

    @pytest.mark.parametrize("target", [0, -1, float("nan"), float("inf"), True])
    def test_rejects_invalid_target_duration(self, target):
        with pytest.raises(ValueError, match="finite"):
            stretch_to_fill(_track(), target)


class TestAlignToKeyframes:
    def test_chooses_nearest_keyframe_and_preserves_metadata(self):
        track = Track("T", cues=[Cue(1, 1, 2, "x")], created="today")
        result = align_to_keyframes(track, [0.9, 1.05], threshold=0.2)
        assert result[0].start == 1.05
        assert result.created == "today"

    def test_preserves_raw_sub_millisecond_duration(self):
        track = Track("tiny", cues=[Cue(1, 0, 0.0004, "x")])
        result = align_to_keyframes(track, [1.0], threshold=1.0)

        assert result[0].start == 1.0
        assert result[0].end - result[0].start == pytest.approx(0.0004, abs=1e-15)
        assert track[0].start == 0.0

    @pytest.mark.parametrize("threshold", [-1, float("nan"), float("inf"), True])
    def test_rejects_invalid_threshold(self, threshold):
        with pytest.raises(ValueError, match="finite"):
            align_to_keyframes(_track(), [1.0], threshold=threshold)

    @pytest.mark.parametrize("keyframe", [-1, float("nan"), float("inf"), True])
    def test_rejects_invalid_keyframes(self, keyframe):
        with pytest.raises(ValueError, match="keyframes"):
            align_to_keyframes(_track(), [keyframe])
