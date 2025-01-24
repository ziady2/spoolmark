"""Tests for metadata."""

from __future__ import annotations

from subcue.metadata import Metadata, detect_language_hint


class TestMetadata:
    def test_create(self):
        assert Metadata is not None

    def test_copy_exists(self):
        assert hasattr(Metadata, "copy")

    def test_from_dict_exists(self):
        assert hasattr(Metadata, "from_dict")

    def test_is_empty_exists(self):
        assert hasattr(Metadata, "is_empty")

    def test_merge_exists(self):
        assert hasattr(Metadata, "merge")

    def test_to_dict_exists(self):
        assert hasattr(Metadata, "to_dict")

    def test_defaults_are_empty(self):
        assert Metadata().is_empty()

    def test_meaningful_technical_fields_are_not_empty(self):
        assert not Metadata(fps=24).is_empty()
        assert not Metadata(encoding="cp1252").is_empty()


class Test_detect_language_hint:
    def test_callable(self):
        assert callable(detect_language_hint)
