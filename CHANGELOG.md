# Changelog

All notable changes to **subcue** are documented here.

## [0.12.1] - 2026-09-02

### Added

- High-level file I/O with content detection, encoding fallback, ASS export,
  atomic writes, and round trips for all supported subtitle formats.
- Batch importing with ordered per-file success and error records, aggregate
  statistics, and batch validation.
- Diagnostic checks with configurable limits, issue summaries, and health
  scoring.
- Composable cue queries, tooltips, accessibility helpers, text normalisation,
  auto-segmentation, timeline analysis, character mapping, and line wrapping.
- Complete API, CLI, presets, formats, reports, architecture, and tutorial
  documentation.

### Changed

- CLI commands now execute real import, conversion, analysis, shifting,
  merging, concatenation, and validation workflows.
- Track transformations consistently return new tracks without mutating their
  inputs.
- Timing offsets are consistently measured in seconds.

### Fixed

- Merge, split, shift, transform, and reconciliation helpers no longer discard
  results from the immutable-style Track API.
- Timeline density and coverage do not double-count overlapping cue intervals.
- Invalid interval, step, and segmentation limits fail immediately instead of
  risking non-terminating loops.
- Domain errors are constructed with their required context.
- Percentile, percentage, line wrapping, duration formatting, and query state
  edge cases now return correct results.
- Embedded newlines round-trip through the plain-text subtitle format.

## [0.12.0] - 2026-08-28

### Added

- `report_density`: subtitle density analysis over time intervals.
- `reconcile` module for track comparison and merging.
- `--top` support for list-shaped CLI report output.

### Fixed

- ASS parsing handles multi-line dialogue markers correctly.
- SVG timeline rendering handles very short cues.

## [0.11.0] - 2026-07-10

### Added

- `report_conformance` with Netflix, broadcast, and web presets.
- `dedup` module for duplicate cue detection.
- Industry-oriented configuration presets.

## [0.10.0] - 2026-05-15

### Added

- Style-usage and sync-validation reports.
- Text and regular-expression search.

## [0.9.0] - 2026-03-20

### Added

- Track splitting and merging.
- Interpolation and binning utilities.

## [0.8.0] - 2026-01-25

### Added

- SVG timelines and charts.
- Theme and display-formatting helpers.

## [0.7.0] - 2025-11-10

### Added

- Reading-speed, duration, and speaker reports.

## [0.6.0] - 2025-09-05

### Added

- Timing, CPS, overlap, gap, and word reports.

## [0.5.0] - 2025-07-12

### Added

- HTML, ASCII, CSV, and JSON output helpers.

## [0.4.0] - 2025-05-18

### Added

- ASS/SSA, plain-text, and JSON parsing.

## [0.3.0] - 2025-03-22

### Added

- WebVTT parsing/export and speaker/dialogue utilities.

## [0.2.0] - 2025-01-15

### Added

- Core Cue, Track, Style, and Speaker models.
- SRT parsing/export and timecode utilities.

## [0.1.0] - 2024-10-01

### Added

- Initial package, error hierarchy, configuration, and test setup.
