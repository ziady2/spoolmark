"""Focused branch and edge-case coverage for small helper modules."""

from __future__ import annotations

import json
from datetime import date

import pytest

from subcue.accessibility import (
    alt_text_for_chart,
    contrast_check,
    focus_order,
    heading_hierarchy,
    screen_reader_cue,
    screen_reader_table,
    simplify_text,
)
from subcue.charmap import (
    character_frequency,
    clean_subtitle_text,
    decode_html_entities,
    detect_encoding_issues,
    detect_script,
    fix_encoding,
    transliterate_basic,
)
from subcue.cue import Cue
from subcue.dialogue import DialogueLine, build_dialogue, dialogue_ratio, speaker_turns
from subcue.errors import ValidationError
from subcue.html_writer import (
    render_cue_list,
    render_report_table,
    render_track_preview,
    wrap_html_page,
)
from subcue.json_export import (
    export_cues_json,
    export_report_json,
    export_track_json,
    minified_json,
)
from subcue.marker import (
    Marker,
    auto_chapter_markers,
    cues_between_markers,
    markers_in_range,
)
from subcue.math_utils import (
    bucket,
    clamp,
    cumulative_sum,
    mean,
    median,
    percentile,
    round_to,
    safe_divide,
    simple_linear_regression,
    stdev,
    weighted_average,
)
from subcue.speaker import Speaker, extract_speakers
from subcue.style import Style
from subcue.track import Track


def test_accessibility_text_variants_and_empty_table_title():
    assert alt_text_for_chart("line", "two values") == "line chart showing two values."
    assert screen_reader_table([], title="Results") == "Empty table: Results."

    rendered = screen_reader_table(
        [{"name": "Ada", "score": 3}, {"name": "Bob"}],
        title="Scores",
        summary="Two entrants",
    )
    assert rendered.splitlines() == [
        "Table: Scores",
        "Summary: Two entrants",
        "Columns: name, score",
        "Rows: 2",
        "  Row 1: name=Ada, score=3",
        "  Row 2: name=Bob, score=",
    ]


def test_accessibility_cue_description_with_and_without_speaker():
    spoken = Cue(7, 1.25, 3.75, "<i>Hello</i>", speaker="Ada")
    description = screen_reader_cue(spoken)

    assert "Cue 7." in description
    assert "From 00:00:01.250 to 00:00:03.750." in description
    assert "Duration 2.5 seconds." in description
    assert "Speaker: Ada." in description
    assert description.endswith("Text: Hello")
    assert "Speaker:" not in screen_reader_cue(Cue(1, 0, 1, "Silent"))


def test_accessibility_contrast_focus_headings_and_decorations():
    low = contrast_check("#777777", "#777777")
    assert low == {
        "ratio": 1.0,
        "aa_normal": False,
        "aa_large": False,
        "aaa_normal": False,
    }
    assert contrast_check("bad", "#000000")["ratio"] == 1.0

    elements = [
        {"id": "last", "position": {"x": 3, "y": 2}},
        {"id": "middle", "position": {"x": 2, "y": 0}},
        {"id": "first"},
    ]
    assert [item["id"] for item in focus_order(elements)] == ["first", "middle", "last"]
    assert [item["id"] for item in elements] == ["last", "middle", "first"]

    hierarchy = heading_hierarchy([(2, "Skipped start"), (1, "Reset"), (2, "Child")])
    assert [entry["valid"] for entry in hierarchy] == [False, True, True]

    decorated = "│─┌┐└┘═█░▒▓"
    assert simplify_text(decorated) == "|-++++=#..#"


def test_charmap_repairs_entities_and_reports_every_occurrence():
    broken_quote = "\u00e2\u0080\u0099"
    text = f"{broken_quote}x{broken_quote}"

    assert fix_encoding(text) == "’x’"
    issues = detect_encoding_issues(text)
    assert [issue["position"] for issue in issues] == [0, 4]
    assert all(issue["suggestion"] == "’" for issue in issues)

    encoded = "&gt;&quot;&apos;&nbsp;&#39;&#34;&#65;&#x42;"
    assert decode_html_entities(encoded) == ">\"' '\"AB"
    assert clean_subtitle_text(f"{broken_quote}&amp;") == "’&"


def test_charmap_transliteration_frequency_and_all_script_buckets():
    assert transliterate_basic("café naïve") == "cafe naive"
    assert character_frequency("b a\nb\t") == {"b": 2, "a": 1}

    examples = {
        "latin": "Hello",
        "arabic": "مرحبا",
        "cjk": "中文",
        "cyrillic": "Привет",
        "devanagari": "नमस्ते",
        "other": "123!",
    }
    for expected, sample in examples.items():
        assert detect_script(sample) == expected
    assert detect_script(" \n\t") == "other"
    assert detect_script("abcم") == "latin"


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        ({"text": 1}, "text"),
        ({"speaker": 1}, "speaker"),
        ({"style": 1}, "style"),
    ],
)
def test_cue_rejects_non_string_payload_fields(kwargs, field):
    values = {"text": "text", "speaker": "speaker", "style": "style"}
    values.update(kwargs)

    with pytest.raises(ValidationError, match=field):
        Cue(1, 0, 1, values["text"], speaker=values["speaker"], style=values["style"])


def test_cue_derived_values_comparison_and_metadata_preservation():
    cue = Cue(3, 1.1111, 3.4444, "<b>Hello</b>\nworld", speaker=" Ada ", style=" Main ")

    assert cue.duration == 2.333
    assert cue.mid == 2.278
    assert cue.plain_text == "Hello\nworld"
    assert cue.line_count == 2
    assert cue.speaker == "Ada"
    assert cue.style == "Main"
    assert cue != Cue(4, 1.1111, 3.4444, "different")
    assert cue.__eq__(object()) is NotImplemented

    scaled = cue.scale(2)
    assert (scaled.start, scaled.end, scaled.speaker, scaled.style) == (
        2.2222,
        6.8888,
        "Ada",
        "Main",
    )
    assert cue.with_text("new").speaker == "Ada"
    assert cue.with_speaker("Bob").style == "Main"


@pytest.mark.parametrize("offset", [True, "1", float("nan"), float("inf")])
def test_cue_shift_rejects_invalid_offsets(offset):
    with pytest.raises(ValidationError, match="offset"):
        Cue(1, 1, 2, "x").shift(offset)


def test_cue_shift_clamps_both_ends_and_touching_ranges_do_not_overlap():
    shifted = Cue(1, 1, 2, "x", speaker="A", style="S").shift(-10)
    touching = Cue(2, 2, 3, "y")

    assert (shifted.start, shifted.end, shifted.speaker, shifted.style) == (0, 0, "A", "S")
    assert not Cue(1, 0, 2, "x").overlaps(touching)
    assert Cue(1, 0, 2, "x").gap_to(Cue(2, 1, 3, "y")) == -1


def test_dialogue_line_round_trip_repr_and_speaker_identity():
    cues = [
        Cue(1, 0, 1, "<i>Hello</i>", speaker="Alice"),
        Cue(2, 1, 2, "Again", speaker="alice"),
        Cue(3, 2, 3, "Narration"),
    ]
    dialogue = build_dialogue(cues)

    assert len(dialogue) == 2
    assert dialogue[0].speaker is dialogue[1].speaker
    assert "Alice" in repr(dialogue[0])
    assert "Hello" in repr(dialogue[0])

    restored = DialogueLine.from_dict(dialogue[0].to_dict())
    assert restored.cue == dialogue[0].cue
    assert restored.speaker == dialogue[0].speaker


def test_dialogue_turns_empty_case_insensitivity_and_ratio_rounding():
    assert speaker_turns([]) == []
    lines = [
        DialogueLine(Cue(1, 0, 1, "a"), Speaker("Alice")),
        DialogueLine(Cue(2, 1, 2, "b"), Speaker("ALICE")),
        DialogueLine(Cue(3, 2, 3, "c"), Speaker("Bob")),
    ]
    assert speaker_turns(lines) == [
        {"speaker": "Alice", "cue_count": 2},
        {"speaker": "Bob", "cue_count": 1},
    ]
    cues = [Cue(i, i, i + 1, "x", speaker="A" if i == 1 else "") for i in range(1, 4)]
    assert dialogue_ratio(cues) == 0.333


def test_html_cue_list_escapes_content_and_obeys_visibility_flags():
    cue = Cue(2, 0, 1, "<b>A&B</b>", speaker="A&B")
    rendered = render_cue_list([cue])

    assert '<span class="idx">2</span>' in rendered
    assert '<span class="speaker">A&amp;B</span>' in rendered
    assert "&lt;b&gt;A&amp;B&lt;/b&gt;" in rendered

    plain = render_cue_list([cue], show_index=False, show_speaker=False)
    assert "<span" not in plain
    assert plain.startswith('<div class="cue">')
    assert render_cue_list([]) == ""


def test_html_report_table_empty_inferred_and_explicit_columns():
    assert render_report_table([]) == "<table><tr><td>No data</td></tr></table>"

    inferred = render_report_table([{"name": "<Ada>", "score": 5}])
    assert "<th>name</th><th>score</th>" in inferred
    assert "&lt;Ada&gt;" in inferred

    explicit = render_report_table([{"name": "Ada"}], columns=["score", "name"])
    assert "<th>score</th><th>name</th>" in explicit
    assert "<td></td><td>Ada</td>" in explicit


def test_html_page_and_track_preview_use_css_defaults_limits_and_escaping():
    custom = wrap_html_page("<p>trusted body</p>", title="A&B", css="body{color:red}")
    assert custom.startswith("<!DOCTYPE html>")
    assert "<title>A&amp;B</title>" in custom
    assert "<style>body{color:red}</style>" in custom
    assert "<p>trusted body</p>" in custom

    default = wrap_html_page("body")
    assert "font-family:sans-serif" in default

    track = Track(
        "<Main>",
        cues=[Cue(1, 0, 1, "first"), Cue(2, 1, 2, "second")],
        language="EN",
    )
    preview = render_track_preview(track, max_cues=1)
    assert "Preview – &lt;Main&gt;" in preview
    assert "Track: <strong>&lt;Main&gt;</strong> | Language: en | Cues: 2" in preview
    assert "first" in preview and "second" not in preview

    untitled = render_track_preview(Track("", language=""))
    assert "<strong>untitled</strong>" in untitled
    assert "Language: unknown" in untitled


def test_json_exports_preserve_metadata_counts_unicode_and_compactness():
    cue = Cue(1, 0, 2, "café", speaker="Ada", style="Main")
    track = Track("French", cues=[cue], language="fr", created="2026-09-05")

    payload = json.loads(export_track_json(track, indent=None))
    assert payload["created"] == "2026-09-05"
    assert payload["duration"] == 2
    assert payload["cue_count"] == 1
    assert payload["cues"][0] == {
        "index": 1,
        "start": 0.0,
        "end": 2.0,
        "text": "café",
        "speaker": "Ada",
        "style": "Main",
        "duration": 2.0,
        "char_count": 4,
        "word_count": 1,
    }
    assert "\\u00e9" in export_track_json(track, ensure_ascii=True)

    assert json.loads(export_cues_json([cue], indent=None))[0]["text"] == "café"
    assert json.loads(export_cues_json([])) == []
    assert minified_json({"a": [1, 2]}) == '{"a":[1,2]}'


def test_json_report_stringifies_supported_fallbacks_and_rejects_nan():
    report = json.loads(export_report_json({"day": date(2026, 9, 5)}, indent=None))
    assert report == {"day": "2026-09-05"}
    assert minified_json({"day": date(2026, 9, 5)}) == '{"day":"2026-09-05"}'

    with pytest.raises(ValueError, match="JSON compliant"):
        export_report_json({"value": float("nan")})
    with pytest.raises(ValueError, match="JSON compliant"):
        minified_json(float("inf"))


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        ({"label": 1}, "label"),
        ({"marker_type": 1}, "marker_type"),
        ({"notes": 1}, "notes"),
    ],
)
def test_marker_rejects_non_string_fields(kwargs, field):
    values = {"label": "Label", "marker_type": "chapter", "notes": "note"}
    values.update(kwargs)

    with pytest.raises(ValidationError, match=field):
        Marker(1, values["label"], marker_type=values["marker_type"], notes=values["notes"])


def test_marker_protocol_round_trip_copy_and_normalization():
    marker = Marker(2, " Scene ", marker_type=" SCENE ", notes=" note ")

    assert (marker.label, marker.marker_type, marker.notes) == ("Scene", "scene", "note")
    assert repr(marker) == "Marker(2.0s, 'Scene')"
    assert marker.__eq__(object()) is NotImplemented
    assert hash(marker) == hash(Marker(2, "Scene"))

    restored = Marker.from_dict(marker.to_dict())
    copied = marker.copy()
    assert restored == marker and restored.to_dict() == marker.to_dict()
    assert copied == marker and copied is not marker


def test_marker_ranges_cue_windows_shift_clamp_and_auto_chapters():
    markers = [Marker(0, "A"), Marker(5, "B"), Marker(10, "C")]
    assert markers_in_range(markers, 0, 5) == markers[:2]

    cues = [Cue(1, 0, 2, "a"), Cue(2, 5, 7, "b"), Cue(3, 10, 12, "c")]
    assert cues_between_markers(cues, markers[0], markers[2]) == cues[:2]

    shifted = Marker(2, "A", marker_type="scene", notes="n").shift(-10)
    assert shifted.to_dict() == {
        "time": 0.0,
        "label": "A",
        "marker_type": "scene",
        "notes": "n",
    }
    assert auto_chapter_markers([]) == []
    assert [m.to_dict() for m in auto_chapter_markers(cues, interval=5)] == [
        {"time": 0.0, "label": "Chapter 1", "marker_type": "chapter", "notes": ""},
        {"time": 5.0, "label": "Chapter 2", "marker_type": "chapter", "notes": ""},
        {"time": 10.0, "label": "Chapter 3", "marker_type": "chapter", "notes": ""},
    ]


def test_math_helpers_cover_empty_swapped_clamped_and_fallthrough_cases():
    assert clamp(5, 10, 0) == 5
    assert percentile([7], 20) == 7
    assert percentile([0, 10], -20) == 0
    assert percentile([0, 10], 120) == 10
    assert mean([]) == 0.0
    assert median([]) == 0.0
    assert stdev([]) == 0.0
    assert safe_divide(2, 0, default=-1) == -1
    assert round_to(1.234, 1) == 1.2
    assert cumulative_sum([0.1, 0.2]) == [0.1, 0.3]
    assert bucket(30, [10, 20, 30]) == 3


def test_regression_and_weighted_average_validation_degenerate_cases():
    with pytest.raises(ValueError, match="equal length"):
        simple_linear_regression([1, 2], [3])
    assert simple_linear_regression([2, 2], [4, 6]) == (0.0, 5.0)

    with pytest.raises(ValueError, match="equal length"):
        weighted_average([1], [1, 2])
    assert weighted_average([10, 20], [0, 0]) == 0.0


def test_speaker_protocol_copy_display_and_normalized_attributes():
    speaker = Speaker(" Ada ", voice_id=" voice ", color=" #ABCDEF ", language=" EN ")

    assert speaker.to_dict() == {
        "name": "Ada",
        "voice_id": "voice",
        "color": "#abcdef",
        "language": "en",
    }
    assert repr(speaker) == "Speaker('Ada')"
    assert speaker.display() == "Ada [en]"
    assert Speaker("Bob").display() == "Bob"
    assert speaker.__eq__(object()) is NotImplemented
    assert hash(speaker) == hash(Speaker("ADA"))

    copied = speaker.copy()
    assert copied == speaker and copied.to_dict() == speaker.to_dict()
    assert copied is not speaker


def test_extract_speakers_ignores_blanks_deduplicates_and_sorts():
    class Anonymous:
        pass

    cues = [
        Anonymous(),
        Cue(1, 0, 1, "x", speaker="zoe"),
        Cue(2, 1, 2, "x"),
        Cue(3, 2, 3, "x", speaker="Ada"),
        Cue(4, 3, 4, "x", speaker="ZOE"),
    ]
    assert [speaker.name for speaker in extract_speakers(cues)] == ["Ada", "zoe"]


def test_style_protocol_serialization_css_and_alignment_fallback():
    style = Style(
        " Main ",
        font_name=" Inter ",
        font_size=24,
        primary_color=" #ABCDEF ",
        bold=True,
        italic=True,
        underline=True,
        alignment=99,
        margin_l=1,
        margin_r=2,
        margin_v=3,
        outline=1.5,
        shadow=0.5,
    )

    assert repr(style) == "Style('Main', 'Inter', 24)"
    assert style.__eq__(object()) is NotImplemented
    assert hash(style) == hash(Style("Main"))
    assert style.primary_color == "#abcdef"
    assert style.alignment_label() == "bottom-center"
    assert style.css() == (
        "font-family: Inter; font-size: 24px; color: #abcdef; font-weight: bold; font-style: italic"
    )

    restored = Style.from_dict(style.to_dict())
    copied = style.copy()
    assert restored.to_dict() == style.to_dict()
    assert copied.to_dict() == style.to_dict()
    assert copied is not style
