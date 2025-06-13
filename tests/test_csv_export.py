"""Tests for csv_export."""

from __future__ import annotations

import csv
import io

from subcue.csv_export import export_cues_csv, export_rows_csv, export_track_csv
from subcue.cue import Cue
from subcue.track import Track


def _track():
    return Track(
        "T",
        cues=[
            Cue(1, 0, 2, "Hello world", speaker="A"),
            Cue(2, 3, 6, "Second cue here", speaker="B"),
            Cue(3, 7, 8, "Short", speaker="A"),
        ],
    )


class TestExportTrackCsv:
    def test_basic(self):
        csv = export_track_csv(_track())
        assert "index" in csv and "Hello world" in csv

    def test_metadata_cannot_inject_physical_rows(self):
        track = Track("safe\n=CMD()", cues=[Cue(1, 0, 1, "x")], language="en\r\n@bad")
        rendered = export_track_csv(track)
        assert "\n=CMD()\n" not in rendered
        assert "\n@bad\n" not in rendered

    def test_text_cells_are_safe_for_spreadsheet_import(self):
        rendered = export_cues_csv([Cue(1, 0, 1, "=2+2", speaker=" @SUM(A1:A2)")])
        row = list(csv.DictReader(io.StringIO(rendered)))[0]
        assert row["text"] == "'=2+2"
        assert row["speaker"] == "'@SUM(A1:A2)"


class TestExportRowsCsv:
    def test_basic(self):
        csv = export_rows_csv([{"a": 1, "b": "x"}])
        assert "a" in csv

    def test_empty(self):
        assert export_rows_csv([]) == ""

    def test_generic_string_cells_are_spreadsheet_safe(self):
        rendered = export_rows_csv([{"value": "+1+1", "number": -3}])
        row = list(csv.DictReader(io.StringIO(rendered)))[0]
        assert row == {"value": "'+1+1", "number": "-3"}
