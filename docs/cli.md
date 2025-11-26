# CLI reference

```text
subcue [-V] [-q] {import,export,analyze,shift,merge,validate,info} ...
```

`-V` prints the package version. `-q` suppresses status messages written to
stderr when a command creates a file; it does not hide requested data written
to stdout. The single-input commands accept `-` to read stdin. `export` and
`shift`, plus the output side of `merge`, accept `-` to write stdout.

Commands return 0 on success, 1 when `validate` finds issues, and 2 for an
invalid file, encoding, format, option, or output operation.

## `import`

Parse a subtitle and print a track summary as JSON.

```bash
subcue import movie.srt
subcue import captions.data --format vtt --encoding utf-8
subcue import - --format srt --compact < movie.srt
```

The input format is inferred by default. Explicit choices are `srt`, `vtt`,
`ass`, `json`, and `txt`.

## `export`

Parse one subtitle and serialise it to another format.

```bash
subcue export movie.srt --format vtt --output movie.vtt
subcue export movie.srt --output report.html
subcue export captions.ssa --format json
```

Output choices are `srt`, `vtt`, `ass`, `json`, `txt`, `csv`, and `html`.
When `--format` is omitted, a file destination's extension decides the format;
stdout keeps the input format. Existing files require `--force`.

## `analyze`

Run a report and print JSON. The syntax is `analyze TYPE FILE`.

```bash
subcue analyze cps movie.srt --top 10
subcue analyze overlap movie.vtt
subcue analyze summary movie.ass --compact
```

Report types are `timing`, `cps`, `overlap`, `gaps`, `words`, `speakers`,
`duration`, `readspeed`, `sync`, `conformance`, `styles`, `density`, and
`summary`. `--top N` limits list-shaped reports; zero means no limit.

## `shift`

Shift every cue by an offset measured in seconds. Negative results clamp to
zero without creating invalid cue ranges.

```bash
subcue shift 2.5 movie.srt --output delayed.srt
subcue shift -1.0 movie.vtt --format srt > earlier.srt
```

The input format is retained unless `--format` or an output extension selects
another one.

## `merge`

Combine two or more files. Chronological mode sorts all cues by start time.
Concatenate mode rebases each later track after the previous one and can insert
a gap.

```bash
subcue merge english.srt commentary.vtt -o combined.srt
subcue merge part1.srt part2.srt --mode concatenate --gap 1.5 -o full.vtt
```

Use `--input-format` only when every input shares a format that cannot be
inferred from its extension. `--name` sets the resulting track name. Merge
inputs must be file paths; stdin is not accepted as one of the input files.

## `validate`

Find structural, ordering, overlap, gap, duration, CPS, line-count, and
line-length issues.

```bash
subcue validate movie.srt
subcue validate movie.srt --preset netflix --json
subcue validate movie.srt --max-cps 22 --max-line-length 45 --compact --json
```

Presets are `netflix`, `broadcast`, and `web`. Individual threshold flags
override the selected preset. Human-readable output is the default; `--json`
returns the score and full issue records.

## `info`

```bash
subcue info
```

Prints the subcue version, Python/runtime platform, and supported input and
output formats.
