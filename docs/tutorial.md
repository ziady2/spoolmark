# Tutorial: Getting Started with subcue

## 1. Parsing your first subtitle file

```python
from subcue.srt_import import parse_srt_text

srt_content = """
1
00:00:01,000 --> 00:00:04,000
Welcome to our video.

2
00:00:05,500 --> 00:00:08,200
In this tutorial, we'll learn about subtitles.

3
00:00:10,000 --> 00:00:13,500
Let's get started!
"""

track = parse_srt_text(srt_content)
print(f"Parsed {len(track)} cues")
print(f"Total duration: {track.duration:.1f}s")
```

## 2. Inspecting cues

Each cue has timing information, text, and computed properties:

```python
for cue in track:
    print(f"Cue {cue.index}: {cue.start:.1f}s - {cue.end:.1f}s")
    print(f"  Duration: {cue.duration:.2f}s")
    print(f"  CPS: {cue.cps:.1f}")
    print(f"  Text: {cue.plain_text}")
    print()
```

## 3. Analysing readability

Characters Per Second (CPS) is the key metric for subtitle readability.
Higher CPS means the viewer has less time to read:

```python
from subcue.report_cps import cps_per_cue

rows = cps_per_cue(track)
for row in rows:
    status = "OK" if row.get("cps", 0) <= 20 else "TOO FAST"
    print(f"Cue {row.get('index', '?')}: {row.get('cps', 0):.1f} CPS - {status}")
```

## 4. Checking for overlaps

Overlapping subtitles cause display issues. subcue detects them:

```python
pairs = track.overlapping_pairs()
if pairs:
    for a, b in pairs:
        print(f"Cue {a.index} and {b.index} overlap!")
else:
    print("No overlaps found.")
```

## 5. Shifting timecodes

If your subtitles are out of sync, shift them:

```python
# Shift forward by 2.5 seconds
shifted = track.shift(2.5)

# Shift backward by 1 second
shifted = track.shift(-1.0)

# Scale for frame rate conversion (25fps to 24fps)
scaled = track.scale(25.0 / 24.0)
```

## 6. Filtering cues

Use the Query builder for complex filters:

```python
from subcue.query import Query

# Find all cues from a specific speaker
narrator_cues = (Query(track)
    .where_speaker("NARRATOR")
    .sort_by("start")
    .execute())

# Find long cues with high CPS
problematic = (Query(track)
    .where_min_duration(5.0)
    .where_min_cps(20)
    .execute())
```

## 7. Converting between formats

```python
from subcue.io import parse_track, serialize_track

# Parse once, then serialise the same track as WebVTT
track = parse_track(srt_content, "srt", name="Tutorial")
vtt_text = serialize_track(track, "vtt")
print(vtt_text)
```

## 8. Running diagnostics

The diagnostic module checks for common issues:

```python
from subcue.diagnostic import run_diagnostics, health_score

issues = run_diagnostics(track)
for issue in issues:
    print(f"[{issue['severity']}] {issue['message']}")

score = health_score(track)
print(f"Health score: {score['score']}/100")
```

## 9. Generating reports

subcue has 13 built-in report types. Detail reports return row dictionaries;
the combined summary returns one nested dictionary:

```python
from subcue.report_timing import timing_per_cue
from subcue.report_cps import cps_per_cue
from subcue.report_summary import full_summary

# Per-cue timing breakdown
rows = timing_per_cue(track)

# Full track summary
summary = full_summary(track)
print(f"Cues: {summary['cue_count']}")
print(f"Total duration: {summary['total_duration']}s")
```

## 10. Exporting results

Export to various formats:

```python
from subcue.io import serialize_track, write_track

# Strings are useful for APIs and pipelines
csv_text = serialize_track(track, "csv")
json_text = serialize_track(track, "json")
html_page = serialize_track(track, "html")

# File writes are atomic and protect existing paths by default
write_track(track, "preview.html")
```

## 11. Batch processing

Process multiple files at once:

```python
from subcue.batch import batch_import, batch_stats, batch_validate

# Parse multiple formats while retaining per-file errors
result = batch_import(["episode-1.srt", "episode-2.vtt"])
print(result.succeeded, result.failed)

# Summarise and validate the successful tracks
stats = batch_stats(result)
validation = batch_validate(result, max_cps=20)
```

## 12. Working with speakers

For dialogue-heavy content like interviews:

```python
from subcue.dialogue import build_dialogue, speaker_turns

# Build structured dialogue
dialogue = build_dialogue(track.cues)

# Analyse speaker turns
turns = speaker_turns(dialogue)
for turn in turns:
    print(f"{turn['speaker']}: {turn['cue_count']} cue(s)")
```

## Next steps

- Read the [API Reference](api.md) for complete documentation
- Check [Conformance Presets](presets.md) for industry standards
- See the [examples/](../examples/) directory for more code samples
