# Reports Reference

## Overview

Report functions return dictionaries with stable, documented keys. Most return
`list[dict]`, even for a one-row aggregate. The sole nested result is
`report_summary.full_summary`, which returns one `dict`. This makes outputs
easy to serialise, render, and test.

## Parameters and row limits

The Python report functions do not share a universal `top` parameter. Use the
function-specific options below, or slice a returned list. The CLI's
`subcue analyze ... --top N` option applies that slicing for list-shaped
reports.

- `cps_outliers(..., threshold=25.0)` sets the CPS cutoff.
- `long_gaps(..., threshold=5.0)` sets the gap cutoff in seconds.
- `word_frequency(..., top_n=50)` limits frequency rows.
- `duration_buckets(..., boundaries=None)` selects bucket boundaries.
- `duration_extremes(..., n=10)` limits shortest/longest rows.
- `readspeed_check` and `readspeed_summary` accept CPS, WPS, and duration limits.
- `density_over_time` and `density_summary` accept `interval=30.0` seconds.

## report_timing

Timing statistics per cue.
Functions: `timing_summary`, `timing_per_cue`, `timing_quartiles`.

## report_cps

Characters-per-second analysis — the key readability metric.
Functions: `cps_per_cue`, `cps_summary`, `cps_outliers`.

## report_overlap

Detect cues with overlapping time ranges.
Functions: `find_overlaps`, `overlap_summary`.

## report_gaps

Analyse silence gaps between consecutive cues.
Functions: `gap_analysis`, `gap_summary`, `long_gaps`.

## report_words

Word and character frequency across all cues.
Functions: `word_frequency`, `char_stats`, `vocabulary_summary`.

## report_speakers

Speaker distribution and dialogue turn analysis.
Functions: `speaker_distribution`, `speaker_turns`, `speaker_timing`.

## report_duration

Cue duration distribution in time buckets.
Functions: `duration_buckets`, `duration_extremes`.

## report_readspeed

Reading speed conformance against CPS threshold.
Functions: `readspeed_check`, `readspeed_summary`.

## report_sync

Combined sync validation (overlaps + gaps + timing issues).
Functions: `sync_issues`, `sync_summary`.

## report_conformance

Standards conformance (CPS, lines, duration limits).
Functions: `conformance_check`, `conformance_summary`.

## report_styles

Style usage analysis for ASS tracks.
Functions: `style_usage`, `style_summary`, `style_transitions`.

## report_density

Subtitle density over time intervals.
Functions: `density_over_time`, `density_summary`.

## report_summary

Comprehensive track summaries with quality scoring. `summary_rows` and
`quality_breakdown` return lists; `full_summary` returns one nested dictionary.
Functions: `full_summary`, `summary_rows`, `quality_breakdown`.

## Usage Example

```python
from subcue.srt_import import parse_srt_file
from subcue.report_cps import cps_per_cue
from subcue.report_summary import full_summary

track = parse_srt_file("movie.srt")

# Per-cue CPS analysis
rows = cps_per_cue(track)
for row in rows:
    if row.get("cps", 0) > 25:
        print(f"Cue {row['index']}: {row['cps']:.1f} CPS (too fast)")

# Full summary
summary = full_summary(track)
print(f"Quality score: {summary['quality']['score']}/100")
```
