# FAQ

**Does subcue need runtime dependencies?**

No. Production code uses only the Python standard library. Pytest, coverage,
Ruff, and build tooling are development dependencies.

**Which subtitle formats are supported?**

Subcue reads SRT, WebVTT, ASS/SSA, JSON, and its line-oriented TXT format. It
writes those formats plus CSV and HTML.

**What is CPS?**

Characters per second is the visible character count divided by cue duration.
A common guideline is 20–25 CPS, but the right limit depends on language,
audience, and delivery platform.

## Parsing

**How are encodings handled?**

`subcue.io.load_track` first tries UTF-8 with optional BOM handling. Automatic
mode also recognises BOM-marked UTF-16 and can fall back to Windows CP1252.
Pass an explicit `encoding=` when the source's encoding is known.

**Can subcue read a URL?**

No. It accepts local paths, strings through the Python parsing functions, or
stdin through CLI commands. Network access is intentionally outside its scope.

**How can encoding artefacts in already-decoded text be cleaned?**

Use `subcue.charmap.detect_encoding_issues` to inspect text and
`subcue.charmap.fix_encoding` for its conservative replacements. OCR-oriented
normalisation is available from `subcue.normalize`.

## Timing and analysis

**How do I shift all timecodes?**

Run `subcue shift 2.5 movie.srt -o delayed.srt`, or call
`track.shift(2.5)`. Offsets are seconds; negative results clamp to zero.

**How do I detect overlapping cues?**

Call `track.overlapping_pairs()` for Cue pairs, use
`subcue.report_overlap.find_overlaps(track)` for report rows, or run
`subcue validate movie.srt` for a combined diagnostic.

**How do I check overall quality?**

`subcue.diagnostic.health_score(track)` returns a deterministic 0–100 score and
severity counts. `run_diagnostics(track)` returns each underlying issue.

**Can I generate charts?**

Yes. `svg_renderer` produces SVG bar, line, and timeline charts;
`ascii_renderer` provides text charts and tables.

## Export

**How do I convert SRT to VTT?**

Use `subcue export movie.srt -o movie.vtt`, or load and serialise the track:

```python
from subcue.io import load_track, serialize_track

vtt = serialize_track(load_track("movie.srt"), "vtt")
```

**Can I export to PDF?**

Not directly. Export a complete HTML preview and print it to PDF with a
browser or document tool.

## Batch processing

**How do I process multiple files?**

`subcue.batch.batch_import(paths)` returns a list-like result containing
successful tracks, ordered records, and isolated per-file errors.

**Can I validate many tracks at once?**

Yes. `batch_validate(tracks, max_cps=20)` returns one result row per track,
including issue and severity counts.
