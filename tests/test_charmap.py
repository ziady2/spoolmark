"""Tests for charmap."""

from __future__ import annotations

from subcue.charmap import (
    character_frequency,
    clean_subtitle_text,
    decode_html_entities,
    detect_encoding_issues,
    detect_script,
    fix_encoding,
    is_rtl,
    transliterate_basic,
)


class TestFixEncoding:
    def test_basic(self):
        result = fix_encoding("hello")
        assert result == "hello"


class TestDecodeHtmlEntities:
    def test_basic(self):
        assert decode_html_entities("&amp;") == "&"
        assert decode_html_entities("&lt;") == "<"

    def test_numeric(self):
        assert decode_html_entities("&#65;") == "A"


class TestDetectEncodingIssues:
    def test_clean(self):
        assert detect_encoding_issues("hello") == []


class TestTransliterate:
    def test_basic(self):
        assert transliterate_basic("cafe") == "cafe"


class TestCharacterFrequency:
    def test_basic(self):
        freq = character_frequency("hello")
        assert freq["l"] == 2


class TestDetectScript:
    def test_latin(self):
        assert detect_script("Hello world") == "latin"

    def test_arabic(self):
        assert detect_script("\u0645\u0631\u062d\u0628\u0627") == "arabic"


class TestIsRtl:
    def test_arabic(self):
        assert is_rtl("\u0645\u0631\u062d\u0628\u0627") is True

    def test_english(self):
        assert is_rtl("Hello") is False


class TestCleanSubtitleText:
    def test_basic(self):
        result = clean_subtitle_text("&amp; hello")
        assert "& hello" == result
