"""Tests for shift."""

from __future__ import annotations

import math

import pytest

from subcue.cue import Cue
from subcue.errors import ValidationError
from subcue.shift import (
    clamp_times,
    scale_track,
    shift_track,
    snap_to_frame,
    snap_to_frames,
    sync_to_reference,
)
from subcue.track import Track


def _track():
    return Track(
        "T",
        cues=[
            Cue(1, 0, 2, "Hello world", speaker="A"),
            Cue(2, 3, 6, "Second subtitle here", speaker="B"),
            Cue(3, 7, 8, "Short one", speaker="A"),
        ],
    )


class Test_clamp_times:
    def test_callable(self):
        assert callable(clamp_times)

    def test_returns_clamped_cues_without_mutating_source(self):
        track = _track()
        result = clamp_times(track, min_time=1.0, max_time=7.5)
        assert [(c.start, c.end) for c in result] == [
            (1.0, 2.0),
            (3.0, 6.0),
            (7.0, 7.5),
        ]
        assert track[0].start == 0.0

    @pytest.mark.parametrize(
        ("minimum", "maximum"),
        [
            (math.nan, None),
            (-1, None),
            (0, math.nan),
            (2, 1),
            (1, 1),
            (False, None),
        ],
    )
    def test_rejects_invalid_ranges_even_for_empty_tracks(self, minimum, maximum):
        with pytest.raises(ValidationError):
            clamp_times(Track("empty"), min_time=minimum, max_time=maximum)


class Test_scale_track:
    def test_callable(self):
        assert callable(scale_track)

    @pytest.mark.parametrize("factor", [-1, 0, math.nan, math.inf, True])
    def test_rejects_invalid_factor_for_empty_track(self, factor):
        with pytest.raises(ValidationError):
            scale_track(Track("empty"), factor)


class Test_shift_track:
    def test_callable(self):
        assert callable(shift_track)

    def test_offset_is_measured_in_seconds(self):
        result = shift_track(_track(), 1.5)
        assert result[0].start == 1.5

    @pytest.mark.parametrize("offset", [math.nan, math.inf, True])
    def test_rejects_invalid_offset_for_empty_track(self, offset):
        with pytest.raises(ValidationError):
            shift_track(Track("empty"), offset)


class Test_snap_to_frame:
    def test_callable(self):
        assert callable(snap_to_frame)


class Test_snap_to_frames:
    def test_callable(self):
        assert callable(snap_to_frames)

    def test_returns_snapped_cues(self):
        track = Track("T", cues=[Cue(1, 0.06, 1.06, "x")])
        result = snap_to_frames(track, fps=10.0)
        assert (result[0].start, result[0].end) == (0.1, 1.1)
        assert track[0].start == 0.06

    @pytest.mark.parametrize("fps", [0, -1, math.nan, math.inf, True])
    def test_rejects_invalid_fps_for_empty_track(self, fps):
        with pytest.raises(ValueError, match="fps"):
            snap_to_frames(Track("empty"), fps=fps)


class Test_sync_to_reference:
    def test_callable(self):
        assert callable(sync_to_reference)

    def test_maps_track_to_reference_range_in_seconds(self):
        track = Track("T", cues=[Cue(1, 10, 12, "a"), Cue(2, 18, 20, "b")])
        result = sync_to_reference(track, 2.0, 6.0)
        assert result[0].start == 2.0
        assert result[-1].end == 6.0

    @pytest.mark.parametrize(
        ("ref_start", "ref_end"),
        [
            (-1, 2),
            (2, 2),
            (3, 2),
            (math.nan, 2),
            (0, math.inf),
            (False, 2),
        ],
    )
    def test_rejects_invalid_reference_for_empty_track(self, ref_start, ref_end):
        with pytest.raises(ValidationError):
            sync_to_reference(Track("empty"), ref_start, ref_end)

    def test_rejects_a_zero_span_target(self):
        target = Track("point", cues=[Cue(1, 4, 4, "still")])
        with pytest.raises(ValidationError, match="span"):
            sync_to_reference(target, 2, 6)
