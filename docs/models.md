# Data Model Reference

## Core classes

### Cue

The fundamental unit of a subtitle. Every subtitle event is a Cue with
start time, end time, text content, and optional speaker/style attributes.

| Attribute | Type | Description |
|-----------|------|-------------|
| index | int | 1-based sequence number |
| start | float | Start time in seconds |
| end | float | End time in seconds |
| text | str | Subtitle text (may contain tags and newlines) |
| speaker | str | Speaker attribution (optional) |
| style | str | Style identifier for ASS format (optional) |

Computed properties: duration, mid, cps, plain_text, char_count, word_count, line_count.

Methods: to_dict, from_dict, copy, shift, scale, overlaps, gap_to, with_text, with_speaker.

### Track

An ordered sequence of Cues representing one subtitle stream.

| Attribute | Type | Description |
|-----------|------|-------------|
| name | str | Track label |
| cues | list[Cue] | Ordered list of subtitle cues |
| language | str | ISO-639 language code |
| created | str | ISO-8601 creation date |

Computed: duration, total_text_length.

Methods: sorted_cues, reindex, shift, scale, add_cue, remove_cue,
filter_by_speaker, overlapping_pairs, timeline_pairs, to_dict, from_dict, copy,
summary.

### Style

Font and formatting for ASS/SSA subtitles.

| Attribute | Type | Default |
|-----------|------|---------|
| name | str | Default |
| font_name | str | Arial |
| font_size | int | 20 |
| primary_color | str | #ffffff |
| bold | bool | False |
| italic | bool | False |
| underline | bool | False |
| alignment | int | 2 (bottom-center) |
| margin_l | int | 10 |
| margin_r | int | 10 |
| margin_v | int | 10 |
| outline | float | 2.0 |
| shadow | float | 1.0 |

### Speaker

| Attribute | Type | Description |
|-----------|------|-------------|
| name | str | Display name |
| voice_id | str | Unique voice ID |
| color | str | Hex colour for display |
| language | str | Speaker language |

### DialogueLine

A `cue` explicitly paired with a `speaker` object.

### Project

Multi-track subtitle container (`name`, `tracks`, `fps`, and `created`) with
immutable-style add/remove helpers and aggregate summaries.

### Marker

Chapter or scene marker (`time`, `label`, `marker_type`, and `notes`).

### Metadata

File-level information including title, language, author, source, frame rate,
encoding, format version, creation time, and notes.

## Serialisation

Every model class implements `to_dict()` and `from_dict()`. `Cue`, `Track`,
`Style`, `Speaker`, `Project`, `Marker`, and `Metadata` also provide `copy()`;
`DialogueLine` can be recreated with `DialogueLine.from_dict()`.

## Immutability Pattern

Model methods that modify data always return NEW objects. The originals
are never mutated. This makes the API safe and predictable.

```python
shifted = track.shift(2.5)
assert track is not shifted
assert track.cues[0].start != shifted.cues[0].start
```
