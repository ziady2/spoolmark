# Timing & CPS Guide

## Timecodes

subcue stores all times internally as `float` seconds. Timecodes are
converted on import and formatted on export.

### Supported formats

| Format | Example | Used by |
|--------|---------|---------|
| SRT | `00:01:23,456` | SubRip |
| VTT | `00:01:23.456` | WebVTT |
| ASS | `0:01:23.45` | ASS/SSA (centiseconds) |
| Short | `1:23.456` | Some editors |
| Plain | `83.456` | Internal/API |

## Characters Per Second (CPS)

CPS measures readability — how fast the viewer must read.

```
CPS = character_count / duration_seconds
```

### Built-in conformance presets

| Standard | Max CPS | Max lines | Max line length |
|----------|---------|-----------|-----------------|
| Netflix | 17 | 2 | 42 chars |
| Broadcast TV | 20 | 2 | 37 chars |
| Web video | 25 | 3 | 60 chars |

These are the values returned by `subcue.presets`. The diagnostic defaults are
20 CPS, 2 lines, and 42 characters per line when no preset is selected.

### `cps_per_cue` ratings

| Range | Status | Meaning |
|-------|--------|---------|
| 0–15 | `ok` | Comfortable reading speed |
| >15–25 | `warn` | Fast, may be hard to follow |
| >25 | `error` | Too fast for the built-in CPS report |

## Duration guidelines

- **Minimum duration**: 0.7–1.0 seconds (viewer needs time to register)
- **Maximum duration**: 6–7 seconds (should not linger too long)
- **Minimum gap**: 0.04–0.17 seconds (flash between cues)

## Reading speed formula

```
Words Per Second (WPS) = word_count / duration
Words Per Minute (WPM) = WPS × 60
```

Average comfortable reading speed: 150–200 WPM (2.5–3.3 WPS).
