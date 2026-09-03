# subcue

> A pure-Python toolkit for parsing, validating, analysing, transforming, and
> converting subtitle files.

[![tests](https://github.com/ziady2/spoolmark/actions/workflows/tests.yml/badge.svg)](https://github.com/ziady2/spoolmark/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Features

- Parse SubRip (`.srt`), WebVTT (`.vtt`), ASS/SSA (`.ass`/`.ssa`), JSON, and
  line-oriented text subtitles.
- Detect formats from extensions or content and decode UTF-8, UTF-16, and
  common Windows text files.
- Export SRT, VTT, ASS, JSON, TXT, CSV, and complete HTML previews.
- Run timing, reading-speed, overlap, gap, word, speaker, style, density, and
  conformance reports.
- Diagnose structural and readability problems with configurable thresholds
  and a deterministic health score.
- Shift, scale, split, merge, concatenate, deduplicate, query, and normalise
  tracks without mutating the source objects.
- Import and validate batches while retaining ordered, per-file error details.
- Use the complete feature set from Python or the command line.
- Run the production package with no third-party runtime dependencies.

## Installation

```bash
git clone https://github.com/ziady2/spoolmark.git
cd subcue
python -m pip install -e ".[dev]"
```

Python 3.9 through 3.13 is supported.

## Command-line quick start

Every command reads a real input file. A single dash (`-`) can be used as the
input or output to stream subtitle data through a shell pipeline.

```bash
# Parse an SRT file and print a JSON summary
subcue import movie.srt

# Convert a subtitle; the output format is inferred from the destination
subcue export movie.srt -o movie.vtt

# Print the ten highest-priority CPS rows as JSON
subcue analyze cps movie.srt --top 10

# Shift timecodes by 2.5 seconds and keep SRT output
subcue shift 2.5 movie.srt -o movie-shifted.srt

# Chronologically merge tracks, or concatenate them with a one-second gap
subcue merge english.srt commentary.srt -o combined.srt
subcue merge part-1.srt part-2.srt --mode concatenate --gap 1 -o full.srt

# Validate using built-in thresholds or an industry preset
subcue validate movie.srt
subcue validate movie.srt --preset netflix --json
```

Output files are protected by default. Pass `--force` to replace an existing
file. Expected file, format, or decoding errors produce a concise diagnostic
and exit status 2; validation findings use exit status 1.

See [the CLI reference](docs/cli.md) for every option.

## Python API quick start

### Load, inspect, and write a track

```python
from subcue.io import load_track, write_track

track = load_track("movie.srt")
print(f"Loaded {len(track)} cues covering {track.duration:.1f}s")

shifted = track.shift(2.5)
write_track(shifted, "movie-shifted.vtt")
```

`write_track` writes through a temporary sibling file and atomically replaces
the destination only when `overwrite=True` is requested.

### Analyse readability

```python
from subcue.report_cps import cps_per_cue
from subcue.report_summary import full_summary

for row in cps_per_cue(track):
    if row["rating"] != "ok":
        print(f"Cue {row['index']}: {row['cps']:.1f} CPS ({row['rating']})")

summary = full_summary(track)
print(f"Quality: {summary['quality']['score']}/100")
```

### Diagnose and process batches

```python
from subcue.batch import batch_import, batch_stats, batch_validate
from subcue.diagnostic import health_score, run_diagnostics

issues = run_diagnostics(track, max_cps=20, max_chars_per_line=42)
score = health_score(track)
print(f"Health: {score['score']}/100 ({len(issues)} issues)")

result = batch_import(["episode-1.srt", "episode-2.vtt"])
print(f"Imported {result.succeeded}; failed {result.failed}")
print(batch_stats(result))
print(batch_validate(result, max_cps=20))
```

### Search and filter

```python
from subcue.query import Query

long_narrator_cues = (
    Query(track)
    .where_speaker("NARRATOR")
    .where_min_duration(3.0)
    .sort_by("duration", reverse=True)
    .execute()
)
```

## Reports

| Report | Description |
|---|---|
| `timing` | Per-cue and aggregate duration statistics |
| `cps` | Characters-per-second analysis |
| `overlap` | Overlapping cue detection |
| `gaps` | Gaps between consecutive cues |
| `words` | Word frequency and character statistics |
| `speakers` | Speaker distribution and dialogue turns |
| `duration` | Cue-duration distribution |
| `readspeed` | Configurable CPS/WPS conformance |
| `sync` | Ordering, overlap, and timing anomalies |
| `conformance` | Common subtitle layout constraints |
| `styles` | ASS style use and transitions |
| `density` | Subtitle coverage over fixed intervals |
| `summary` | Combined track and quality summary |

## Development

```bash
# Fast local suite
python -m pytest -q

# Coverage and lint checks used in CI
python -m pytest --cov=subcue --cov-report=term-missing
python -m ruff check src tests examples scripts
python -m ruff format --check src tests examples scripts

# Build an sdist and wheel
python -m build
```

The repository contains more than 9,000 physical lines of production Python
across 70 modules, plus a behavioral test suite and runnable examples. See
[the architecture guide](docs/architecture.md) for the module map and
[the contributing guide](docs/contributing.md) for development conventions.

## Documentation

- [Tutorial](docs/tutorial.md)
- [API reference](docs/api.md)
- [CLI reference](docs/cli.md)
- [Subtitle formats](docs/formats.md)
- [Reports](docs/reports.md)
- [Conformance presets](docs/presets.md)
- [CPS and timing guide](docs/timing.md)
- [Architecture](docs/architecture.md)
- [Glossary](docs/glossary.md)
- [FAQ](docs/faq.md)
- [Contributing](docs/contributing.md)

## License

MIT — see [LICENSE](LICENSE).
