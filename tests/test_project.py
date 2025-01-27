"""Tests for project."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.errors import NotFoundError
from subcue.project import Project
from subcue.track import Track


class TestProject:
    def test_basic(self):
        p = Project("Movie")
        assert p.name == "Movie" and len(p) == 0

    def test_add_track(self):
        t = Track("EN", cues=[Cue(1, 0, 1, "Hi")])
        p = Project("M").add_track(t)
        assert len(p) == 1

    def test_remove_track(self):
        t = Track("EN", cues=[Cue(1, 0, 1, "Hi")])
        p = Project("M", tracks=[t]).remove_track("EN")
        assert len(p) == 0

    def test_remove_track_does_not_share_remaining_tracks(self):
        original = Project(
            "M",
            tracks=[
                Track("EN", cues=[Cue(1, 0, 1, "Hi")]),
                Track("FR", cues=[Cue(1, 0, 1, "Salut")]),
            ],
        )
        result = original.remove_track("EN")
        result.tracks[0].cues[0].text = "changed"
        assert original.tracks[1].cues[0].text == "Salut"

    def test_remove_missing_raises(self):
        with pytest.raises(NotFoundError):
            Project("M").remove_track("X")

    def test_get_track(self):
        t = Track("EN")
        p = Project("M", tracks=[t])
        assert p.get_track("EN").name == "EN"

    def test_track_names(self):
        p = Project("M", tracks=[Track("EN"), Track("FR")])
        assert p.track_names() == ["EN", "FR"]

    def test_total_cues(self):
        p = Project("M", tracks=[Track("EN", cues=[Cue(1, 0, 1, "x")])])
        assert p.total_cues() == 1

    def test_to_dict(self):
        d = Project("M").to_dict()
        assert d["name"] == "M"

    def test_copy(self):
        p = Project("M", tracks=[Track("EN")])
        assert len(p.copy()) == 1

    def test_summary(self):
        s = Project("M").summary()
        assert s["track_count"] == 0
