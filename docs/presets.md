# Conformance Presets

subcue includes three built-in starting presets for subtitle conformance
checking. Each preset defines maximum CPS, line count, line length, and timing
constraints. They are software defaults, so confirm the current delivery
specification for the platform receiving the subtitles.

## Netflix-style preset

| Parameter | Value |
|-----------|-------|
| Max CPS | 17 |
| Max lines | 2 |
| Max line length | 42 characters |
| Min duration | 0.833 seconds (20 frames at 24fps) |
| Max duration | 7 seconds |
| Min gap | 0.083 seconds (2 frames at 24fps) |

The built-in `netflix` preset uses the project's strictest CPS limit.

## Broadcast TV

| Parameter | Value |
|-----------|-------|
| Max CPS | 20 |
| Max lines | 2 |
| Max line length | 37 characters |
| Min duration | 1.0 second |
| Max duration | 6 seconds |
| Min gap | 0.1 seconds |

Broadcast standards are designed for live television where viewers may
be distracted. The lower CPS and shorter line lengths help maintain
readability across different screen sizes.

## Web Video

| Parameter | Value |
|-----------|-------|
| Max CPS | 25 |
| Max lines | 3 |
| Max line length | 60 characters |
| Min duration | 0.5 seconds |
| Max duration | 10 seconds |
| Min gap | 0 seconds |

Web video presets are more relaxed, reflecting the smaller screens and
ability to pause/rewind.

## Using presets in subcue

```python
from subcue.presets import get_preset

netflix = get_preset("netflix")
print(netflix)  # {"max_cps": 17.0, "max_lines": 2, ...}

# Use all preset thresholds with the diagnostic engine
from subcue.diagnostic import run_diagnostics
issues = run_diagnostics(
    track,
    max_cps=netflix["max_cps"],
    max_lines=netflix["max_lines"],
    max_chars_per_line=netflix["max_line_length"],
    min_duration=netflix["min_duration"],
    max_duration=netflix["max_duration"],
    min_gap=netflix["min_gap"],
)
```

## CPS by language

Different languages and audiences have different reading speeds. The presets
above are designed as Latin-script starting points. The following ranges are
illustrative rather than enforced by subcue; use the recipient's specification
for delivery work:

| Language | Recommended max CPS |
|----------|---------------------|
| English | 20-25 |
| French | 20-25 |
| German | 20-25 |
| Spanish | 20-25 |
| Japanese | 4-7 (characters) |
| Chinese | 4-7 (characters) |
| Korean | 12-15 |
| Arabic | 18-22 |
| Russian | 18-22 |

## Timing best practices

1. **One sentence per cue** when possible
2. **Break at punctuation** (commas, full stops) rather than mid-word
3. **Balance line lengths** — avoid very short + very long line pairs
4. **Respect shot changes** — avoid spanning cuts when the delivery rules require it
5. **Match dialogue timing** — align cue onset and removal with the spoken audio
6. **Leave intentional gaps** — apply the recipient's minimum-gap requirement
