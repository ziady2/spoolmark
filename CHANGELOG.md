# Changelog

All notable changes to **subcue** are documented here.

## [0.12.0] — 2026-08-28

### Added
- `report_density`: subtitle density analysis over time intervals.
- `reconcile` module for track comparison and merging.
- `--top` flag on all report subcommands.

### Fixed
- ASS parser handles multi-line dialogue with `\N` correctly.
- SVG timeline rendering for very short cues.

## [0.11.0] — 2026-07-10

### Added
- `report_conformance` with Netflix/broadcast presets.
- `dedup` module for duplicate cue detection.
- `presets` module with industry-standard configs.

### Changed
- Reports now copy lists instead of returning references.

## [0.10.0] — 2026-05-15

### Added
- `report_styles`: style usage analysis for ASS tracks.
- `report_sync`: sync validation combining gap/overlap checks.
- `search` module with regex support.

## [0.9.0] — 2026-03-20

### Added
- `split` module for splitting tracks by speaker, time, or gap.
- `merge` module for combining multiple tracks.
- `interpolation` and `binning` utilities.

## [0.8.0] — 2026-01-25

### Added
- Full SVG timeline and chart rendering.
- Theme system with light/dark presets.
- `formatter` module for timecode display formatting.

## [0.7.0] — 2025-11-10

### Added
- `report_readspeed` with configurable CPS thresholds.
- `report_duration` with bucket distribution.
- `report_speakers` with dialogue turn tracking.

## [0.6.0] — 2025-09-05

### Added
- `report_timing`, `report_cps`, `report_overlap`, `report_gaps`.
- `report_words` with character and word frequency.

## [0.5.0] — 2025-07-12

### Added
- HTML cue list renderer.
- ASCII timeline and table renderer.
- CSV and JSON export modules.

## [0.4.0] — 2025-05-18

### Added
- ASS/SSA parser with style extraction.
- Plain-text subtitle parser.
- JSON subtitle format support.

## [0.3.0] — 2025-03-22

### Added
- WebVTT parser and exporter.
- Speaker extraction from cue text.
- Dialogue model and turn analysis.

## [0.2.0] — 2025-01-15

### Added
- `Cue`, `Track`, `Style`, `Speaker` core models.
- SRT parser and exporter.
- `timing` module with timecode parsing.

## [0.1.0] — 2024-10-01

### Added
- Initial project setup.
- `version.py`, `errors.py`, basic `pyproject.toml`.
- pytest configuration and CI workflow.
