"""Command-line interface for loading, converting, and analysing subtitles."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any, Callable, Sequence, TypedDict

from .errors import SubcueError
from .io import (
    INPUT_FORMATS,
    OUTPUT_FORMATS,
    decode_subtitle_bytes,
    detect_format,
    format_from_path,
    load_track,
    normalize_format,
    parse_track,
    serialize_track,
    write_track,
)
from .track import Track
from .version import version_string

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_ERROR = 2


class _DiagnosticOptions(TypedDict):
    max_cps: float
    max_lines: int
    max_chars_per_line: int
    min_duration: float
    max_duration: float
    min_gap: float


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser used by the console entry point."""
    parser = argparse.ArgumentParser(
        prog="subcue",
        description="Parse, analyse, transform, and convert subtitle files.",
    )
    parser.add_argument("-V", "--version", action="version", version=version_string())
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress non-essential status messages",
    )
    subparsers = parser.add_subparsers(dest="command", help="available commands")

    import_parser = subparsers.add_parser(
        "import", help="parse a subtitle and print a JSON summary"
    )
    import_parser.add_argument("file", help="input path, or - for stdin")
    _add_input_options(import_parser, short_format=True)
    import_parser.add_argument("--compact", action="store_true", help="write JSON on one line")

    export_parser = subparsers.add_parser("export", help="convert a subtitle to another format")
    export_parser.add_argument("file", help="input path, or - for stdin")
    export_parser.add_argument(
        "-f",
        "--format",
        choices=OUTPUT_FORMATS,
        help="output format (inferred from --output when omitted)",
    )
    export_parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="output path, or - for stdout (default)",
    )
    _add_input_options(export_parser, option="--input-format")
    export_parser.add_argument(
        "--force", action="store_true", help="replace an existing output file"
    )

    analyze_parser = subparsers.add_parser("analyze", help="run an analysis report and print JSON")
    analyze_parser.add_argument(
        "type",
        choices=(
            "timing",
            "cps",
            "overlap",
            "gaps",
            "words",
            "speakers",
            "duration",
            "readspeed",
            "sync",
            "conformance",
            "styles",
            "density",
            "summary",
        ),
        help="report to run",
    )
    analyze_parser.add_argument("file", help="input path, or - for stdin")
    _add_input_options(analyze_parser, short_format=True)
    analyze_parser.add_argument(
        "--top",
        type=_non_negative_int,
        default=0,
        help="limit list reports to the first N rows (0 means all)",
    )
    analyze_parser.add_argument("--compact", action="store_true", help="write JSON on one line")

    shift_parser = subparsers.add_parser("shift", help="shift every cue by a number of seconds")
    shift_parser.add_argument("offset", type=float, help="seconds (negative = earlier)")
    shift_parser.add_argument("file", help="input path, or - for stdin")
    shift_parser.add_argument("-o", "--output", default="-", help="path or - for stdout")
    shift_parser.add_argument(
        "-f",
        "--format",
        choices=OUTPUT_FORMATS,
        help="output format (defaults to the input format)",
    )
    _add_input_options(shift_parser, option="--input-format")
    shift_parser.add_argument("--force", action="store_true")

    merge_parser = subparsers.add_parser("merge", help="combine subtitle files into one track")
    merge_parser.add_argument("files", nargs="+", help="two or more input paths")
    merge_parser.add_argument("-o", "--output", default="-", help="path or - for stdout")
    merge_parser.add_argument(
        "-f",
        "--format",
        choices=OUTPUT_FORMATS,
        help="output format (inferred from --output when omitted)",
    )
    merge_parser.add_argument(
        "--input-format",
        choices=("auto",) + INPUT_FORMATS,
        default="auto",
        help="format shared by all inputs (default: infer each file)",
    )
    merge_parser.add_argument(
        "--mode",
        choices=("chronological", "concatenate"),
        default="chronological",
        help="sort by time or place tracks end-to-end",
    )
    merge_parser.add_argument(
        "--gap",
        type=_non_negative_float,
        default=0.0,
        help="seconds between tracks in concatenate mode",
    )
    merge_parser.add_argument("--name", default="merged", help="resulting track name")
    merge_parser.add_argument("--force", action="store_true")
    merge_parser.add_argument("--encoding", default="auto")

    validate_parser = subparsers.add_parser(
        "validate", help="find timing, readability, and layout issues"
    )
    validate_parser.add_argument("file", help="input path, or - for stdin")
    _add_input_options(validate_parser, short_format=True)
    validate_parser.add_argument(
        "--preset",
        choices=("netflix", "broadcast", "web"),
        help="start with a built-in threshold preset",
    )
    validate_parser.add_argument("--max-cps", type=_positive_float)
    validate_parser.add_argument("--max-lines", type=_positive_int)
    validate_parser.add_argument("--max-line-length", type=_positive_int)
    validate_parser.add_argument("--min-duration", type=_non_negative_float)
    validate_parser.add_argument("--max-duration", type=_positive_float)
    validate_parser.add_argument("--min-gap", type=_non_negative_float)
    validate_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    validate_parser.add_argument("--compact", action="store_true")

    subparsers.add_parser("info", help="show version and runtime information")
    return parser


def run_command(args: argparse.Namespace) -> int:
    """Execute a parsed command and return a process exit code."""
    command = getattr(args, "command", None)
    if command is None:
        build_parser().print_help()
        return EXIT_OK
    handlers: dict[str, Callable[[argparse.Namespace], int]] = {
        "info": _cmd_info,
        "import": _cmd_import,
        "export": _cmd_export,
        "analyze": _cmd_analyze,
        "shift": _cmd_shift,
        "merge": _cmd_merge,
        "validate": _cmd_validate,
    }
    handler = handlers.get(command)
    if handler is None:
        print(f"subcue: unknown command: {command}", file=sys.stderr)
        return EXIT_ERROR
    return handler(args)


def main(argv: Sequence[str] | None = None) -> None:
    """Console entry point with concise handling for expected user errors."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code = run_command(args)
    except (SubcueError, OSError, UnicodeError, ValueError) as exc:
        print(f"subcue: error: {exc}", file=sys.stderr)
        code = EXIT_ERROR
    raise SystemExit(code)


def _cmd_info(args: argparse.Namespace) -> int:
    print(version_string())
    print(f"Python {platform.python_version()}")
    print(f"Platform {platform.system()} {platform.machine()}".rstrip())
    print(f"Input formats: {', '.join(INPUT_FORMATS)}")
    print(f"Output formats: {', '.join(OUTPUT_FORMATS)}")
    return EXIT_OK


def _cmd_import(args: argparse.Namespace) -> int:
    from .report_summary import full_summary

    track, canonical = _load_source(args.file, args.format, args.encoding)
    payload = full_summary(track)
    payload["source"] = args.file
    payload["format"] = canonical
    _print_json(payload, compact=args.compact)
    return EXIT_OK


def _cmd_export(args: argparse.Namespace) -> int:
    track, input_format = _load_source(args.file, args.input_format, args.encoding)
    output_format = _resolve_output_format(args.format, args.output, fallback=input_format)
    _emit_track(
        track,
        args.output,
        output_format,
        overwrite=args.force,
        quiet=args.quiet,
    )
    return EXIT_OK


def _cmd_analyze(args: argparse.Namespace) -> int:
    track, _ = _load_source(args.file, args.format, args.encoding)
    result = _run_report(args.type, track)
    if args.top and isinstance(result, list):
        result = result[: args.top]
    _print_json(result, compact=args.compact)
    return EXIT_OK


def _cmd_shift(args: argparse.Namespace) -> int:
    track, input_format = _load_source(args.file, args.input_format, args.encoding)
    shifted = track.shift(args.offset)
    output_format = _resolve_output_format(args.format, args.output, fallback=input_format)
    _emit_track(
        shifted,
        args.output,
        output_format,
        overwrite=args.force,
        quiet=args.quiet,
    )
    return EXIT_OK


def _cmd_merge(args: argparse.Namespace) -> int:
    if len(args.files) < 2:
        raise ValueError("merge requires at least two input files")
    format_override = None if args.input_format == "auto" else args.input_format
    tracks = [
        load_track(path, format_name=format_override, encoding=args.encoding) for path in args.files
    ]
    if args.mode == "concatenate":
        from .merge import concatenate_tracks

        merged = concatenate_tracks(tracks, name=args.name, gap=args.gap)
    else:
        from .merge import merge_tracks

        merged = merge_tracks(tracks, name=args.name)
    first_format = _format_for_file(args.files[0], format_override, args.encoding)
    output_format = _resolve_output_format(args.format, args.output, fallback=first_format)
    _emit_track(
        merged,
        args.output,
        output_format,
        overwrite=args.force,
        quiet=args.quiet,
    )
    return EXIT_OK


def _cmd_validate(args: argparse.Namespace) -> int:
    from .diagnostic import health_score, run_diagnostics

    track, _ = _load_source(args.file, args.format, args.encoding)
    thresholds = _validation_thresholds(args)
    diagnostic_options: _DiagnosticOptions = {
        "max_cps": float(thresholds["max_cps"]),
        "max_lines": int(thresholds["max_lines"]),
        "max_chars_per_line": int(thresholds["max_chars_per_line"]),
        "min_duration": float(thresholds["min_duration"]),
        "max_duration": float(thresholds["max_duration"]),
        "min_gap": float(thresholds["min_gap"]),
    }
    issues = run_diagnostics(track, **diagnostic_options)
    score = health_score(track, **diagnostic_options)
    payload = {
        "source": args.file,
        "track": track.name,
        "valid": not issues,
        "issue_count": len(issues),
        "health": score,
        "issues": issues,
    }
    if args.json:
        _print_json(payload, compact=args.compact)
    else:
        _print_validation_text(payload)
    return EXIT_OK if not issues else EXIT_ISSUES


def _load_source(
    source: str,
    requested_format: str | None,
    encoding: str,
) -> tuple[Track, str]:
    format_name = None if requested_format in (None, "auto") else requested_format
    if source != "-":
        track = load_track(source, format_name=format_name, encoding=encoding)
        canonical = _format_for_file(source, format_name, encoding)
        return track, canonical
    text = sys.stdin.read()
    if not text:
        raise ValueError("stdin is empty")
    canonical = normalize_format(format_name) if format_name else detect_format(text)
    return parse_track(text, canonical, name="stdin"), canonical


def _format_for_file(source: str, format_name: str | None, encoding: str) -> str:
    """Resolve a file's input format, falling back to content detection."""
    if format_name is not None:
        return normalize_format(format_name)
    try:
        return format_from_path(source)
    except SubcueError:
        data = Path(source).read_bytes()
        text, _ = decode_subtitle_bytes(data, encoding=encoding)
        return detect_format(text, filename=source)


def _resolve_output_format(
    requested_format: str | None,
    output: str,
    *,
    fallback: str,
) -> str:
    if requested_format:
        return normalize_format(requested_format, for_output=True)
    if output != "-":
        return format_from_path(output, for_output=True)
    return normalize_format(fallback, for_output=True)


def _emit_track(
    track: Track,
    output: str,
    format_name: str,
    *,
    overwrite: bool,
    quiet: bool,
) -> None:
    if output == "-":
        rendered = serialize_track(track, format_name)
        sys.stdout.write(rendered)
        if rendered and not rendered.endswith("\n"):
            sys.stdout.write("\n")
        return
    destination = write_track(track, output, format_name=format_name, overwrite=overwrite)
    if not quiet:
        print(f"wrote {len(track)} cues to {destination}", file=sys.stderr)


def _run_report(report_type: str, track: Track) -> Any:
    if report_type == "summary":
        from .report_summary import full_summary

        return full_summary(track)

    from .report_conformance import conformance_check
    from .report_cps import cps_per_cue
    from .report_density import density_over_time
    from .report_duration import duration_buckets
    from .report_gaps import gap_analysis
    from .report_overlap import find_overlaps
    from .report_readspeed import readspeed_check
    from .report_speakers import speaker_distribution
    from .report_styles import style_usage
    from .report_sync import sync_issues
    from .report_timing import timing_per_cue
    from .report_words import word_frequency

    reports: dict[str, Callable[[Track], Any]] = {
        "timing": timing_per_cue,
        "cps": cps_per_cue,
        "overlap": find_overlaps,
        "gaps": gap_analysis,
        "words": word_frequency,
        "speakers": speaker_distribution,
        "duration": duration_buckets,
        "readspeed": readspeed_check,
        "sync": sync_issues,
        "conformance": conformance_check,
        "styles": style_usage,
        "density": density_over_time,
    }
    try:
        report = reports[report_type]
    except KeyError as exc:
        raise ValueError(f"unknown report type: {report_type}") from exc
    return report(track)


def _validation_thresholds(args: argparse.Namespace) -> dict[str, float | int]:
    values: dict[str, float | int] = {
        "max_cps": 20.0,
        "max_lines": 2,
        "max_chars_per_line": 42,
        "min_duration": 0.7,
        "max_duration": 7.0,
        "min_gap": 0.04,
    }
    if args.preset:
        from .presets import get_preset

        preset = get_preset(args.preset)
        values.update(
            {
                "max_cps": preset["max_cps"],
                "max_lines": preset["max_lines"],
                "max_chars_per_line": preset["max_line_length"],
                "min_duration": preset["min_duration"],
                "max_duration": preset["max_duration"],
                "min_gap": preset["min_gap"],
            }
        )
    overrides = {
        "max_cps": args.max_cps,
        "max_lines": args.max_lines,
        "max_chars_per_line": args.max_line_length,
        "min_duration": args.min_duration,
        "max_duration": args.max_duration,
        "min_gap": args.min_gap,
    }
    values.update({key: value for key, value in overrides.items() if value is not None})
    if float(values["min_duration"]) > float(values["max_duration"]):
        raise ValueError("--min-duration cannot exceed --max-duration")
    return values


def _print_json(value: Any, *, compact: bool = False) -> None:
    indent = None if compact else 2
    separators = (",", ":") if compact else None
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=indent,
            separators=separators,
            default=str,
            sort_keys=False,
        )
    )


def _print_validation_text(payload: dict[str, Any]) -> None:
    health = payload["health"]
    score = health.get("score", 0) if isinstance(health, dict) else health
    print(f"Track: {payload['track']}")
    print(f"Health score: {score}/100")
    if payload["valid"]:
        print("No issues found.")
        return
    print(f"Issues: {payload['issue_count']}")
    for issue in payload["issues"]:
        severity = str(issue.get("severity", "warning")).upper()
        code = issue.get("code", issue.get("issue_type", "issue"))
        cue = issue.get("cue_index")
        prefix = f"cue {cue}: " if cue is not None else ""
        message = issue.get("message", issue.get("detail", ""))
        print(f"- {severity} {code}: {prefix}{message}")


def _add_input_options(
    parser: argparse.ArgumentParser,
    *,
    short_format: bool = False,
    option: str = "--format",
) -> None:
    flags = ("-f", option) if short_format else (option,)
    parser.add_argument(
        *flags,
        choices=("auto",) + INPUT_FORMATS,
        default="auto",
        help="input format (default: infer from extension/content)",
    )
    parser.add_argument(
        "--encoding",
        default="auto",
        help="text encoding (default: auto-detect UTF-8/UTF-16/CP1252)",
    )


def _positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return value


def _non_negative_int(raw: str) -> int:
    value = int(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return value


def _positive_float(raw: str) -> float:
    value = float(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return value


def _non_negative_float(raw: str) -> float:
    value = float(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return value


__all__ = [
    "EXIT_ERROR",
    "EXIT_ISSUES",
    "EXIT_OK",
    "build_parser",
    "main",
    "run_command",
]
