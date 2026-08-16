"""Tests for normalize."""

from __future__ import annotations

import pytest

from subcue.cue import Cue
from subcue.normalize import (
    capitalize_sentences,
    fix_common_ocr_errors,
    normalize_cue_text,
    normalize_dashes,
    normalize_ellipsis,
    normalize_quotes,
    normalize_track,
    normalize_whitespace,
    remove_duplicate_lines,
    strip_hearing_impaired,
    strip_speaker_prefix,
)
from subcue.track import Track


class TestNormalizeQuotes:
    def test_fancy_quotes(self):
        assert normalize_quotes("\u201cHi\u201d") == '"Hi"'

    def test_plain(self):
        assert normalize_quotes('"Hi"') == '"Hi"'


class TestNormalizeDashes:
    def test_em_dash(self):
        assert normalize_dashes("a\u2014b") == "a--b"


class TestNormalizeEllipsis:
    def test_ascii_ellipsis(self):
        assert normalize_ellipsis("Wait... What...") == "Wait\u2026 What\u2026"

    def test_existing_unicode_ellipsis_is_unchanged(self):
        assert normalize_ellipsis("Wait\u2026") == "Wait\u2026"


class TestNormalizeWhitespace:
    def test_basic(self):
        assert normalize_whitespace("  a   b  ") == "a b"


class TestStripHearingImpaired:
    def test_brackets(self):
        assert strip_hearing_impaired("[music] Hello").strip() == "Hello"

    def test_parens(self):
        assert strip_hearing_impaired("(laughing) Hi").strip() == "Hi"


class TestStripSpeakerPrefix:
    def test_basic(self):
        assert strip_speaker_prefix("JOHN: Hello") == "Hello"


class TestFixOcr:
    def test_basic(self):
        assert fix_common_ocr_errors("l'm fine") == "I'm fine"

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("l", "I"),
            ("l'd", "I'd"),
            ("l'll", "I'll"),
            ("lt's", "It's"),
            ("lf", "If"),
            ("ln", "In"),
        ],
    )
    def test_corrects_only_complete_ocr_tokens(self, source, expected):
        assert fix_common_ocr_errors(source) == expected

    def test_handles_tokens_next_to_punctuation_and_line_breaks(self):
        assert fix_common_ocr_errors("l, lf!\nln?") == "I, If!\nIn?"

    def test_does_not_corrupt_embedded_letter_sequences(self):
        text = "golf shelf kiln sunlight l'amour"
        assert fix_common_ocr_errors(text) == text


class TestCapitalize:
    def test_basic(self):
        assert capitalize_sentences("hello. world.") == "Hello. World."


class TestRemoveDuplicateLines:
    def test_basic(self):
        assert remove_duplicate_lines("a\na\nb") == "a\nb"


class TestNormalizeCueText:
    def test_combined(self):
        result = normalize_cue_text("  \u201cHello\u201d   world  ")
        assert '"Hello"' in result

    def test_includes_ellipsis_normalization(self):
        assert normalize_cue_text("  Wait...   now  ") == "Wait\u2026 now"

    def test_pipeline_is_idempotent(self):
        once = normalize_cue_text("  \u201cWait...\u201d  ")
        assert normalize_cue_text(once) == once


class TestNormalizeTrack:
    def test_preserves_metadata_and_cue_attributes(self):
        source = Track(
            "English",
            cues=[
                Cue(
                    7,
                    1.0,
                    2.5,
                    "  \u201cWait...\u201d  \r\n  \u201cWait...\u201d  ",
                    speaker="Narrator",
                    style="Italic",
                )
            ],
            language="en",
            created="2026-09-05T12:00:00Z",
        )

        result = normalize_track(source)

        assert result.name == "English"
        assert result.language == "en"
        assert result.created == "2026-09-05T12:00:00Z"
        assert result.cues[0].text == '"Wait\u2026"'
        assert result.cues[0].speaker == "Narrator"
        assert result.cues[0].style == "Italic"
        assert result.cues[0].index == 7
        assert source.cues[0].text.startswith("  \u201c")
