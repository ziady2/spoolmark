"""Tests for json_export."""

from __future__ import annotations

import json

from subcue.cue import Cue
from subcue.json_export import (
    Sequence,
    export_cues_json,
    export_report_json,
    export_track_json,
    minified_json,
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


class Test_Sequence:
    def test_callable(self):
        assert callable(Sequence)


class Test_export_cues_json:
    def test_callable(self):
        assert callable(export_cues_json)


class Test_export_report_json:
    def test_callable(self):
        assert callable(export_report_json)


class Test_export_track_json:
    def test_callable(self):
        assert callable(export_track_json)

    def test_includes_created_metadata(self):
        track = Track("T", cues=[Cue(1, 0, 1, "x")], created="2026-09-05")
        assert json.loads(export_track_json(track))["created"] == "2026-09-05"


class Test_minified_json:
    def test_callable(self):
        assert callable(minified_json)
