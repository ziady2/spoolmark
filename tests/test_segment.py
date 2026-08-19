"""Behavioral tests for markup-aware subtitle segmentation."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from subcue.cue import Cue
from subcue.segment import (
    auto_segment_track,
    estimate_cue_count,
    optimal_break_points,
    segment_text,
)
from subcue.text_utils import strip_all_tags
from subcue.track import Track
from subcue.wordwrap import check_line_lengths


def _visible_words(cues: list[Cue]) -> list[str]:
    text = " ".join(cue.text for cue in cues)
    without_html = re.sub(r"""<(?:(?:"[^"]*")|(?:'[^']*')|[^'">])*>""", "", text)
    return re.sub(r"\{[^}]*\}", "", without_html).split()


def _assert_html_cues_are_balanced(cues: list[Cue]) -> None:
    for cue in cues:
        for line in cue.text.splitlines():
            ET.fromstring(f"<root>{line}</root>")


class TestSegmentText:
    def test_sentence_boundaries_create_contiguous_cues(self):
        cues = segment_text("Hello world. This is a test.", 0, 5)

        assert [cue.text for cue in cues] == ["Hello world.", "This is a test."]
        assert cues[0].start == 0
        assert cues[-1].end == 5
        assert cues[0].end == cues[1].start

    def test_empty_and_whitespace_only_text_create_no_cues(self):
        assert segment_text("", 0, 1) == []
        assert segment_text(" \n\t ", 0, 1) == []

    def test_preserves_all_words_when_splitting(self):
        original = "one two three four five six seven eight nine ten"
        cues = segment_text(
            original,
            0,
            10,
            max_chars_per_line=5,
            max_lines=1,
            min_duration=0,
        )

        assert _visible_words(cues) == original.split()

    def test_every_possible_cue_obeys_width_and_line_limits(self):
        original = "one two three four five six seven eight nine ten"
        cues = segment_text(
            original,
            0,
            10,
            max_chars_per_line=8,
            max_lines=2,
            min_duration=0,
        )

        assert len(cues) > 1
        assert all(
            check_line_lengths(cue.text, max_width=8, max_lines=2)["conformant"] for cue in cues
        )
        assert _visible_words(cues) == original.split()

    def test_explicit_newlines_are_resegmented_without_dropping_text(self):
        cues = segment_text(
            "one\ntwo\nthree",
            0,
            3,
            max_chars_per_line=10,
            max_lines=2,
            min_duration=0,
        )

        assert _visible_words(cues) == ["one", "two", "three"]
        assert all(len(cue.text.splitlines()) <= 2 for cue in cues)

    def test_overlong_token_is_intact_and_isolated(self):
        token = "extraordinary"
        cues = segment_text(
            f"one {token} two",
            0,
            3,
            max_chars_per_line=5,
            max_lines=1,
            min_duration=0,
        )

        assert [strip_all_tags(cue.text) for cue in cues] == ["one", token, "two"]
        assert len(strip_all_tags(cues[1].text)) > 5

    def test_allocates_entire_range_with_no_gaps_and_minimums(self):
        cues = segment_text(
            "one two three four five six seven eight",
            2,
            12,
            max_chars_per_line=8,
            max_lines=1,
            min_duration=0.7,
        )

        assert cues[0].start == 2
        assert cues[-1].end == 12
        assert all(left.end == right.start for left, right in zip(cues, cues[1:]))
        assert all(cue.end - cue.start >= 0.7 - 1e-12 for cue in cues)

    def test_exact_minimum_budget_is_supported(self):
        cues = segment_text(
            "one two",
            0,
            1.4,
            max_chars_per_line=3,
            max_lines=1,
            min_duration=0.7,
        )

        assert [(cue.start, cue.end) for cue in cues] == [(0.0, 0.7), (0.7, 1.4)]

    def test_visible_text_drives_proportional_duration(self):
        cues = segment_text(
            "<i>Hi.</i> This sentence is longer.",
            0,
            10,
            min_duration=0,
        )

        assert len(cues) == 2
        assert cues[1].duration > cues[0].duration

    def test_rejects_impossible_minimum_duration(self):
        with pytest.raises(ValueError, match="cannot each fit"):
            segment_text(
                "one two three four five six",
                0,
                1,
                max_chars_per_line=5,
                max_lines=1,
                min_duration=0.7,
            )

    def test_balances_html_at_every_line_and_cue_boundary(self):
        original = '<font color="red" title="a > b"><i>one two three four five six</i></font>'
        cues = segment_text(
            original,
            0,
            6,
            max_chars_per_line=7,
            max_lines=1,
            min_duration=0,
        )

        assert _visible_words(cues) == ["one", "two", "three", "four", "five", "six"]
        assert all(
            check_line_lengths(cue.text, max_width=7, max_lines=1)["conformant"] for cue in cues
        )
        assert all('title="a > b"' in cue.text for cue in cues)
        _assert_html_cues_are_balanced(cues)

    def test_ass_override_blocks_remain_atomic(self):
        original = r"{\i1}one two three four five{\i0}"
        cues = segment_text(
            original,
            0,
            5,
            max_chars_per_line=5,
            max_lines=1,
            min_duration=0,
        )
        combined = " ".join(cue.text for cue in cues)

        assert combined.count(r"{\i1}") == 1
        assert combined.count(r"{\i0}") == 1
        assert _visible_words(cues) == ["one", "two", "three", "four", "five"]
        assert all(token.count("{") == token.count("}") for token in combined.split())

    @pytest.mark.parametrize(
        "arguments",
        [
            ("text", True, 1),
            ("text", -1, 1),
            ("text", float("nan"), 1),
            ("text", 0, float("inf")),
            ("text", 1, 1),
        ],
    )
    def test_rejects_invalid_time_ranges(self, arguments):
        with pytest.raises(ValueError):
            segment_text(*arguments)

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"max_chars_per_line": 0},
            {"max_chars_per_line": 2.5},
            {"max_chars_per_line": True},
            {"max_lines": 0},
            {"max_lines": 1.5},
            {"min_duration": -1},
            {"min_duration": float("nan")},
            {"min_duration": True},
        ],
    )
    def test_rejects_invalid_limits(self, kwargs):
        with pytest.raises(ValueError):
            segment_text("text", 0, 1, **kwargs)

    def test_rejects_non_string_text(self):
        with pytest.raises(TypeError, match="text must be a string"):
            segment_text(None, 0, 1)  # type: ignore[arg-type]


class TestAutoSegmentTrack:
    def test_segments_and_preserves_all_track_and_cue_metadata(self):
        cue = Cue(
            8,
            1,
            11,
            "one two three four five six seven eight",
            speaker="NARRATOR",
            style="emphasis",
        )
        track = Track("English", cues=[cue], language="EN", created="2026-01-01")
        result = auto_segment_track(
            track,
            max_chars_per_line=7,
            max_lines=1,
            min_duration=0,
        )

        assert len(result.cues) > 1
        assert result.name == "English"
        assert result.language == "en"
        assert result.created == "2026-01-01"
        assert [item.index for item in result.cues] == list(range(1, len(result.cues) + 1))
        assert all(item.speaker == "NARRATOR" for item in result.cues)
        assert all(item.style == "emphasis" for item in result.cues)
        assert _visible_words(result.cues) == cue.text.split()

    def test_markup_length_alone_does_not_trigger_segmentation(self):
        text = '<font color="bright red">short</font>'
        track = Track("T", cues=[Cue(4, 0, 1, text, speaker="A", style="B")])
        result = auto_segment_track(track, max_chars_per_line=5, max_lines=1)

        assert len(result.cues) == 1
        assert result.cues[0].text == text
        assert result.cues[0].speaker == "A"
        assert result.cues[0].style == "B"

    def test_minimum_duration_is_forwarded(self):
        track = Track("T", cues=[Cue(1, 0, 1, "one two three")])

        with pytest.raises(ValueError, match="cannot each fit"):
            auto_segment_track(
                track,
                max_chars_per_line=3,
                max_lines=1,
                min_duration=0.7,
            )

    def test_rejects_non_track_input(self):
        with pytest.raises(TypeError, match="track must be a Track"):
            auto_segment_track(None)  # type: ignore[arg-type]


class TestEstimateCueCount:
    def test_estimates_from_visible_characters(self):
        assert estimate_cue_count("A" * 200) == 3
        assert estimate_cue_count("<i>1234</i>", max_chars=4) == 1

    def test_normalizes_whitespace_and_handles_empty_text(self):
        assert estimate_cue_count("  hello\nworld  ", max_chars=11) == 1
        assert estimate_cue_count("<i></i>") == 0

    @pytest.mark.parametrize("value", [0, -1, 1.5, True])
    def test_rejects_invalid_capacity(self, value):
        with pytest.raises(ValueError):
            estimate_cue_count("text", max_chars=value)


class TestOptimalBreakPoints:
    def test_prefers_sentence_boundary_within_window(self):
        assert optimal_break_points("Hello. next words here", max_width=12)[0] == 6

    def test_indices_never_fall_inside_html_or_ass_tags(self):
        text = r'<i title="a > b">Hello wonderful</i> {\b1}world again and more'
        breaks = optimal_break_points(text, max_width=10)
        tag_spans = [match.span() for match in re.finditer(r"<.*?>|\{.*?\}", text)]

        assert breaks
        assert breaks == sorted(set(breaks))
        assert all(not any(start < point < end for start, end in tag_spans) for point in breaks)

    def test_trailing_overlong_token_has_no_hard_character_break(self):
        assert optimal_break_points("extraordinary", max_width=5) == []

    def test_leading_overlong_token_breaks_at_next_word_boundary(self):
        text = "extraordinary next"
        assert optimal_break_points(text, max_width=5) == [len("extraordinary ")]

    @pytest.mark.parametrize("value", [0, -1, 1.5, True])
    def test_rejects_invalid_width(self, value):
        with pytest.raises(ValueError):
            optimal_break_points("some text", max_width=value)
