"""Tests for json_import."""

from __future__ import annotations

import json

import pytest

from subcue.errors import ParseError
from subcue.json_import import parse_json_file, parse_json_text, track_to_json


class TestParseJsonText:
    def test_object(self):
        data = json.dumps({"name": "T", "cues": [{"index": 1, "start": 0, "end": 1, "text": "Hi"}]})
        t = parse_json_text(data)
        assert len(t) == 1

    def test_array(self):
        data = json.dumps([{"index": 1, "start": 0, "end": 1, "text": "Hi"}])
        t = parse_json_text(data)
        assert len(t) == 1

    def test_empty_raises(self):
        with pytest.raises(ParseError):
            parse_json_text("")

    def test_bad_json_raises(self):
        with pytest.raises(ParseError):
            parse_json_text("{bad}")

    def test_no_cues_raises(self):
        with pytest.raises(ParseError):
            parse_json_text("[]")

    def test_bom(self):
        data = "\ufeff" + json.dumps([{"index": 1, "start": 0, "end": 1, "text": "x"}])
        assert len(parse_json_text(data)) == 1

    def test_object_metadata_roundtrips(self):
        from subcue.cue import Cue
        from subcue.track import Track

        original = Track(
            "Arabic",
            cues=[Cue(1, 0, 1, "مرحبا")],
            language="ar",
            created="2026-09-05",
        )
        restored = parse_json_text(track_to_json(original))
        assert restored.name == original.name
        assert restored.language == "ar"
        assert restored.created == "2026-09-05"

    @pytest.mark.parametrize(
        "payload",
        [
            {"cues": 42},
            {"cues": [{"index": "bad", "start": 0, "end": 1, "text": "x"}]},
            {"cues": [{"start": float("nan"), "end": 1, "text": "x"}]},
        ],
    )
    def test_schema_errors_are_reported_as_parse_errors(self, payload):
        with pytest.raises(ParseError):
            parse_json_text(json.dumps(payload))


class TestTrackToJson:
    def test_roundtrip(self):
        from subcue.cue import Cue
        from subcue.track import Track

        t = Track("T", cues=[Cue(1, 0, 1, "Hi")])
        output = track_to_json(t)
        assert "Hi" in output


class TestParseJsonFile:
    def test_file(self, tmp_path):
        p = tmp_path / "t.json"
        p.write_text(json.dumps([{"index": 1, "start": 0, "end": 1, "text": "x"}]))
        assert len(parse_json_file(str(p))) == 1

    def test_missing(self):
        with pytest.raises(ParseError):
            parse_json_file("/nonexistent.json")
