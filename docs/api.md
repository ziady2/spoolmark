# API Reference

## subcue.cue

### Class: Cue

```text
Cue(index: int, start: float, end: float, text: str,
    *, speaker: str = "", style: str = "")
```

**Properties:**
- `duration` → `float` — End minus start in seconds
- `mid` → `float` — Midpoint of the cue
- `cps` → `float` — Characters per second
- `plain_text` → `str` — Text with all tags stripped
- `char_count` → `int` — Character count of plain text
- `word_count` → `int` — Word count of plain text
- `line_count` → `int` — Number of non-empty lines

**Methods:**
- `to_dict()` → `dict` — Serialise to dictionary
- `from_dict(data)` → `Cue` — Create from dictionary
- `copy()` → `Cue` — Deep copy
- `shift(offset)` → `Cue` — Return copy with shifted times
- `scale(factor)` → `Cue` — Return copy with scaled times
- `overlaps(other)` → `bool` — Check time overlap
- `gap_to(other)` → `float` — Gap to next cue (negative = overlap)
- `with_text(new_text)` → `Cue` — Copy with different text
- `with_speaker(new_speaker)` → `Cue` — Copy with different speaker

## subcue.track

### Class: Track

```text
Track(name: str = "Untitled", *, cues: list[Cue] | None = None,
      language: str = "", created: str = "")
```

**Properties:**
- `duration` → `float` — Timeline span (maximum end minus minimum start)
- `total_text_length` → `int` — Sum of character counts

**Methods:**
- `sorted_cues()` → `list[Cue]` — Cues sorted by start time
- `reindex()` → `Track` — Re-number cues from 1
- `shift(offset)` → `Track` — Shift all timecodes
- `scale(factor)` → `Track` — Scale all timecodes
- `add_cue(cue)` → `Track` — Add a cue
- `remove_cue(index)` → `Track` — Remove by index
- `filter_by_speaker(speaker)` → `Track` — Filter to one speaker
- `overlapping_pairs()` → `list[tuple]` — Find overlaps
- `timeline_pairs()` → `list[tuple]` — Pair each cue with the current timeline frontier
- `to_dict()` → `dict` — Serialise
- `from_dict(data)` → `Track` — Deserialise
- `copy()` → `Track` — Deep copy
- `summary()` → `dict` — Quick stats

## subcue.timing

### Functions

- `parse_timecode(raw: str) → float` — Parse "HH:MM:SS,mmm" to seconds
- `format_timecode(seconds: float, *, separator=",") → str` — Format to SRT style
- `format_timecode_vtt(seconds: float) → str` — Format to VTT style
- `format_timecode_ass(seconds: float) → str` — Format to ASS style
- `cps(text: str, duration: float) → float` — Characters per second
- `wps(text: str, duration: float) → float` — Words per second
- `overlap(start_a, end_a, start_b, end_b) → float` — Overlap duration
- `gap(end_a, start_b) → float` — Gap between cues
- `shift_time(seconds, offset) → float` — Shift with clamping
- `scale_time(seconds, factor) → float` — Scale with clamping
- `snap_to_frame(seconds, fps) → float` — Snap to nearest frame
- `format_duration_human(seconds) → str` — "1m 23s" style

## subcue.srt_import

- `parse_srt_text(text, *, name="SRT Track") → Track`
- `parse_srt_file(path, **kwargs) → Track`
- `cues_to_srt(cues) → str`

## subcue.vtt_import

- `parse_vtt_text(text, *, name="VTT Track") → Track`
- `parse_vtt_file(path, **kwargs) → Track`
- `cues_to_vtt(cues) → str`

## subcue.ass_import

- `parse_ass_text(text, *, name="ASS Track") → Track`
- `parse_ass_file(path, **kwargs) → Track`
- `parse_ass_styles(text) → list[Style]`

## subcue.json_import

- `parse_json_text(text, *, name="JSON Track") → Track`
- `parse_json_file(path, **kwargs) → Track`
- `track_to_json(track) → str`

## subcue.txt_import

- `parse_txt_text(text, *, name="TXT Track") → Track`
- `parse_txt_file(path, **kwargs) → Track`
- `cues_to_txt(cues) → str`

## Report Modules

Most report functions accept a `Track` and return a list of detailed or
aggregate row dictionaries. `report_summary.full_summary` is the exception:
it returns one nested dictionary. Optional thresholds are documented on the
individual functions.

```python
def report_function(track: Track, **options: object) -> list[dict]:
    """Return rows with fixed keys."""
    return []
```

### Available reports

| Module | Functions |
|--------|-----------|
| `report_timing` | `timing_summary`, `timing_per_cue`, `timing_quartiles` |
| `report_cps` | `cps_per_cue`, `cps_summary`, `cps_outliers` |
| `report_overlap` | `find_overlaps`, `overlap_summary` |
| `report_gaps` | `gap_analysis`, `gap_summary`, `long_gaps` |
| `report_words` | `word_frequency`, `char_stats`, `vocabulary_summary` |
| `report_speakers` | `speaker_distribution`, `speaker_turns`, `speaker_timing` |
| `report_duration` | `duration_buckets`, `duration_extremes` |
| `report_readspeed` | `readspeed_check`, `readspeed_summary` |
| `report_sync` | `sync_issues`, `sync_summary` |
| `report_conformance` | `conformance_check`, `conformance_summary` |
| `report_styles` | `style_usage`, `style_summary`, `style_transitions` |
| `report_density` | `density_over_time`, `density_summary` |
| `report_summary` | `full_summary`, `summary_rows`, `quality_breakdown` |

## Rendering

- `html_writer.render_cue_list(cues, *, show_index=True, show_speaker=True) → str`
- `html_writer.render_report_table(rows, columns=None) → str`
- `ascii_renderer.bar(value, max_value, width=40, char="#") → str`
- `ascii_renderer.table_string(headers, rows, *, padding=1) → str`
- `svg_renderer.svg_bar_chart(labels, values) → str`
- `svg_renderer.svg_line_chart(values) → str`
- `svg_renderer.svg_timeline(starts, ends) → str`
- `csv_export.export_track_csv(track) → str`
- `json_export.export_track_json(track) → str`

## High-level file I/O

- `io.detect_format(text, *, filename=None) → str`
- `io.load_track(path, *, format_name=None, encoding="auto", name=None) → Track`
- `io.parse_track(text, format_name, *, name="") → Track`
- `io.serialize_track(track, format_name, *, json_indent=2) → str`
- `io.write_track(track, path, *, format_name=None, overwrite=False) → Path`
- `io.cues_to_ass(cues, *, title="Subcue Export") → str`

## Advanced

- `search.search_cues(cues, query) → list[Cue]`
- `search.search_track(track, query) → list[Cue]`
- `merge.merge_tracks(tracks, *, name="merged") → Track`
- `split.split_by_speaker(track) → dict[str, Track]`
- `shift.shift_track(track, offset) → Track`
- `dedup.deduplicate(cues) → list[Cue]`
- `batch.batch_import(paths, format=None, *, on_error="collect") → BatchImportResult`
- `batch.batch_stats(tracks) → list[dict]`
- `batch.batch_validate(tracks, max_cps=20.0, ...) → list[dict]`
- `diagnostic.run_diagnostics(track, *, max_cps=20.0, ...) → list[dict]`
- `diagnostic.health_score(track, *, max_cps=20.0, ...) → dict`
- `diagnostic.issue_summary(track, *, max_cps=20.0, ...) → list[dict]`
- `query.Query(track).where_speaker("A").execute() → list[Cue]`
