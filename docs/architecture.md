# Architecture

## Overview

subcue is a pure-Python toolkit for processing subtitle files. It parses SRT,
VTT, ASS/SSA, JSON, and line-oriented TXT into a unified `Cue`/`Track` model,
then provides analysis reports, transformations, and export capabilities.

## Layer Diagram

```
CLI  (cli.py, __main__.py)
  │
  ├── Reports   (report_*.py)  → structured dictionaries
  ├── Parsers   (*_import.py)  → Track objects
  ├── Exporters (*_export.py, *_renderer.py)
  ├── Workflows (io.py, batch.py, diagnostic.py)
  │
  ├── Data Model (cue, track, style, speaker, dialogue, project, marker, metadata)
  │
  └── Foundation (errors, config, timing, text_utils, math_utils)
```

## Key Concepts

- **Timecodes** are stored as `float` seconds internally
- **Cue** = a single subtitle entry (start, end, text)
- **Track** = ordered list of cues + metadata
- **CPS** = characters per second (key readability metric)
- Reports return structured dictionaries with stable keys; most use
  `list[dict]`, while `full_summary` returns one nested `dict`


## Module Categories

### Foundation and workflows
- version.py - Version information
- errors.py - Package exception hierarchy
- config.py - Configuration with JSON persistence
- text_utils.py - HTML/ASS tag stripping, word count, character count
- math_utils.py - Statistical helpers (mean, median, percentile, regression)
- timing.py - Timecode parsing, formatting, CPS/WPS calculation
- cli.py - argparse-based CLI with 7 subcommands
- __main__.py - python -m subcue entry point
- io.py - Format detection, decoding, parsing dispatch, and atomic writes
- batch.py - Ordered multi-file import, statistics, and validation
- diagnostic.py - Configurable issue detection and health scoring

### Data Model (8 modules)
- cue.py - Cue class with timing, text, speaker, style
- track.py - Track class (ordered cue list with metadata)
- style.py - Style class for ASS formatting properties
- speaker.py - Speaker class and extraction utilities
- dialogue.py - DialogueLine class and turn analysis
- project.py - Multi-track container
- marker.py - Chapter and scene markers
- metadata.py - File-level information (title, language, fps)

### Parsers (5 modules)
- srt_import.py - SubRip (.srt) parser
- vtt_import.py - WebVTT (.vtt) parser
- ass_import.py - ASS/SSA (.ass) parser with style extraction
- txt_import.py - Plain text tab-delimited parser
- json_import.py - JSON subtitle format parser

### Reports (13 modules)
Each exposes structured report functions with documented keys:
- report_timing, report_cps, report_overlap, report_gaps
- report_words, report_speakers, report_duration, report_readspeed
- report_sync, report_conformance, report_styles, report_density
- report_summary (comprehensive track summary)

### Renderers (6 modules)
- html_writer.py - HTML cue list and table output
- ascii_renderer.py - ASCII bars, sparklines, tables, boxes
- svg_renderer.py - SVG bar charts, timelines, line charts
- csv_export.py - CSV serialisation
- json_export.py - JSON serialisation
- table.py - TableBuilder and pivot table utilities

### Theme (4 modules)
- color.py - Color class with hex conversion and luminance
- theme.py - Theme presets (light, dark) with CSS variables
- formatter.py - Number, duration, percentage, CPS formatters
- layout.py - Grid, Section, horizontal rule, page header

### Advanced (16 modules)
- stats.py - Collection-level statistics and correlation
- transform.py - Sorting, filtering, tag stripping
- merge.py - Track merging and concatenation
- shift.py - Time shifting and frame rate conversion
- search.py - Text and regex search with scoring
- split.py - Track splitting by speaker, time, gaps, style
- interpolation.py - Linear interpolation, moving average, smoothing
- binning.py - Equal-width, quantile, and custom binning
- query.py - Composable fluent query builder
- tooltip.py - Chart hover text generators
- accessibility.py - WCAG contrast checks, screen reader helpers
- normalize.py - Text cleaning, OCR fixes, quote normalization
- segment.py - Auto-segmentation and intelligent line breaking
- timeline.py - Coverage analysis, gap detection, compression
- charmap.py - Encoding detection, transliteration, script detection
- wordwrap.py - Intelligent subtitle word wrapping

### Infrastructure (6 modules)
- plugin.py - Plugin registry with handler execution
- presets.py - Industry presets (Netflix, broadcast, web)
- validation.py - Input validation and sanitisation
- dedup.py - Duplicate cue detection and merging
- conversion.py - SRT/VTT conversion helpers
- reconcile.py - Track comparison and conflict detection

## Design Decisions

1. All times stored as float seconds for simplicity
2. Immutable-style API - methods return new objects
3. Reports return dictionary-shaped data for easy serialisation
4. Zero external dependencies - stdlib only
5. Flat test layout enforced by conftest.py
6. Relative imports throughout the package
