# Architecture

## Overview

subcue is a pure-Python toolkit for processing subtitle files. It parses
SRT, VTT, and ASS formats into a unified `Cue`/`Track` model, then
provides analysis reports, transformations, and export capabilities.

## Layer Diagram

```
CLI  (cli.py, __main__.py)
  │
  ├── Reports   (report_*.py)  → List[dict] rows
  ├── Parsers   (*_import.py)  → Track objects
  ├── Exporters (*_export.py, *_renderer.py)
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
- All report functions return `List[dict]` with fixed keys
