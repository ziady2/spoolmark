"""End-to-end tests for the command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

from subcue.cli import EXIT_ERROR, EXIT_ISSUES, EXIT_OK, build_parser, main, run_command
from subcue.srt_import import parse_srt_file

SRT_ONE = """1
00:00:01,000 --> 00:00:03,000
Hello world
"""

SRT_TWO = """1
00:00:00,000 --> 00:00:02,000
First cue

2
00:00:03,000 --> 00:00:05,000
Second cue
"""

SRT_BAD = """1
00:00:00,000 --> 00:00:00,200
This subtitle is much too long to read in only two tenths of a second

2
00:00:00,100 --> 00:00:02,000
Overlap
"""


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "input.srt"
    path.write_text(SRT_TWO, encoding="utf-8")
    return path


def parse_args(*args: str) -> argparse.Namespace:
    return build_parser().parse_args(list(args))


class TestParser:
    def test_program_and_commands(self) -> None:
        parser = build_parser()
        assert parser.prog == "subcue"
        help_text = parser.format_help()
        for command in ("import", "export", "analyze", "shift", "merge", "validate", "info"):
            assert command in help_text

    def test_version_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            build_parser().parse_args(["--version"])
        assert exc.value.code == 0
        assert capsys.readouterr().out.startswith("subcue ")

    @pytest.mark.parametrize(
        "args",
        [
            ("analyze", "cps", "x.srt", "--top", "-1"),
            ("merge", "a.srt", "b.srt", "--gap", "-0.1"),
            ("validate", "x.srt", "--max-cps", "0"),
            ("validate", "x.srt", "--max-lines", "0"),
            ("validate", "x.srt", "--min-gap", "-1"),
        ],
    )
    def test_numeric_validation_rejects_invalid_values(self, args: tuple[str, ...]) -> None:
        with pytest.raises(SystemExit) as exc:
            build_parser().parse_args(args)
        assert exc.value.code == EXIT_ERROR

    def test_merge_parser_requires_at_least_one_path(self) -> None:
        with pytest.raises(SystemExit):
            build_parser().parse_args(["merge"])


class TestDispatch:
    def test_no_command_prints_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert run_command(parse_args()) == EXIT_OK
        assert "available commands" in capsys.readouterr().out

    def test_unknown_command_returns_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        args = argparse.Namespace(command="does-not-exist")
        assert run_command(args) == EXIT_ERROR
        assert "unknown command" in capsys.readouterr().err

    def test_info_reports_runtime_and_formats(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert run_command(parse_args("info")) == EXIT_OK
        output = capsys.readouterr().out
        assert "subcue " in output
        assert "Python " in output
        assert "Input formats: srt, vtt, ass, json, txt" in output
        assert "Output formats:" in output


class TestImportCommand:
    def test_prints_real_summary(self, source: Path, capsys: pytest.CaptureFixture[str]) -> None:
        code = run_command(parse_args("import", str(source)))
        payload = json.loads(capsys.readouterr().out)
        assert code == EXIT_OK
        assert payload["source"] == str(source)
        assert payload["format"] == "srt"
        assert payload["cue_count"] == 2
        assert payload["total_words"] == 4

    def test_unknown_extension_uses_content_detection(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        source = tmp_path / "subtitle.data"
        source.write_text(SRT_ONE, encoding="utf-8")

        assert run_command(parse_args("import", str(source))) == EXIT_OK

        payload = json.loads(capsys.readouterr().out)
        assert payload["format"] == "srt"

    def test_compact_json_has_one_line(
        self, source: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert run_command(parse_args("import", str(source), "--compact")) == EXIT_OK
        output = capsys.readouterr().out
        assert len(output.splitlines()) == 1
        assert json.loads(output)["cue_count"] == 2

    def test_reads_stdin(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(sys, "stdin", __import__("io").StringIO(SRT_ONE))
        assert run_command(parse_args("import", "-")) == EXIT_OK
        assert json.loads(capsys.readouterr().out)["cue_count"] == 1


class TestExportCommand:
    def test_converts_to_vtt_stdout(self, source: Path, capsys: pytest.CaptureFixture[str]) -> None:
        code = run_command(parse_args("export", str(source), "-f", "vtt"))
        output = capsys.readouterr().out
        assert code == EXIT_OK
        assert output.startswith("WEBVTT")
        assert "00:00:03.000" in output

    def test_infers_json_from_output_path(
        self, source: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        destination = tmp_path / "output.json"
        code = run_command(parse_args("export", str(source), "-o", str(destination)))
        assert code == EXIT_OK
        assert json.loads(destination.read_text(encoding="utf-8"))["name"] == "input"
        assert "wrote 2 cues" in capsys.readouterr().err

    def test_quiet_suppresses_file_status(
        self, source: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        destination = tmp_path / "output.vtt"
        args = parse_args("--quiet", "export", str(source), "-o", str(destination))
        assert run_command(args) == EXIT_OK
        assert capsys.readouterr().err == ""

    def test_existing_output_needs_force(self, source: Path, tmp_path: Path) -> None:
        destination = tmp_path / "output.vtt"
        destination.write_text("keep", encoding="utf-8")
        with pytest.raises(Exception, match="already exists"):
            run_command(parse_args("export", str(source), "-o", str(destination)))
        assert destination.read_text(encoding="utf-8") == "keep"
        assert (
            run_command(parse_args("export", str(source), "-o", str(destination), "--force"))
            == EXIT_OK
        )
        assert destination.read_text(encoding="utf-8").startswith("WEBVTT")


class TestAnalyzeCommand:
    @pytest.mark.parametrize(
        "report_type",
        [
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
        ],
    )
    def test_all_report_types_emit_json(
        self,
        report_type: str,
        source: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        code = run_command(parse_args("analyze", report_type, str(source), "--compact"))
        assert code == EXIT_OK
        assert json.loads(capsys.readouterr().out) is not None

    def test_top_limits_list_report(self, source: Path, capsys: pytest.CaptureFixture[str]) -> None:
        code = run_command(parse_args("analyze", "cps", str(source), "--top", "1"))
        assert code == EXIT_OK
        assert len(json.loads(capsys.readouterr().out)) == 1


class TestShiftCommand:
    def test_shifts_in_seconds_to_file(self, source: Path, tmp_path: Path) -> None:
        destination = tmp_path / "shifted.srt"
        args = parse_args("shift", "2.5", str(source), "-o", str(destination))
        assert run_command(args) == EXIT_OK
        shifted = parse_srt_file(str(destination))
        assert shifted[0].start == 2.5
        assert shifted[-1].end == 7.5

    def test_negative_shift_clamps_at_zero(
        self, source: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert run_command(parse_args("shift", "-2", str(source))) == EXIT_OK
        assert "00:00:00,000 --> 00:00:00,000" in capsys.readouterr().out


class TestMergeCommand:
    def test_chronological_merge(self, tmp_path: Path) -> None:
        first = tmp_path / "a.srt"
        second = tmp_path / "b.srt"
        output = tmp_path / "merged.srt"
        first.write_text(SRT_ONE, encoding="utf-8")
        second.write_text(
            SRT_ONE.replace("00:00:01,000", "00:00:04,000").replace("00:00:03,000", "00:00:06,000"),
            encoding="utf-8",
        )
        args = parse_args("merge", str(second), str(first), "-o", str(output))
        assert run_command(args) == EXIT_OK
        merged = parse_srt_file(str(output))
        assert [cue.start for cue in merged] == [1.0, 4.0]
        assert [cue.index for cue in merged] == [1, 2]

    def test_concatenate_mode_applies_gap(self, tmp_path: Path) -> None:
        first = tmp_path / "a.srt"
        second = tmp_path / "b.srt"
        output = tmp_path / "joined.srt"
        first.write_text(SRT_ONE, encoding="utf-8")
        second.write_text(SRT_ONE, encoding="utf-8")
        args = parse_args(
            "merge",
            str(first),
            str(second),
            "--mode",
            "concatenate",
            "--gap",
            "1.5",
            "-o",
            str(output),
        )
        assert run_command(args) == EXIT_OK
        joined = parse_srt_file(str(output))
        assert joined[1].start == pytest.approx(joined[0].end + 1.5)

    def test_run_command_rejects_only_one_input(self, source: Path) -> None:
        with pytest.raises(ValueError, match="at least two"):
            run_command(parse_args("merge", str(source)))


class TestValidateCommand:
    def test_clean_track_exits_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        source = tmp_path / "clean.srt"
        source.write_text(SRT_ONE, encoding="utf-8")
        code = run_command(parse_args("validate", str(source), "--json"))
        payload = json.loads(capsys.readouterr().out)
        assert code == EXIT_OK
        assert payload["valid"] is True
        assert payload["issues"] == []

    def test_bad_track_exits_one_and_lists_issues(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        source = tmp_path / "bad.srt"
        source.write_text(SRT_BAD, encoding="utf-8")
        code = run_command(parse_args("validate", str(source), "--json", "--compact"))
        payload = json.loads(capsys.readouterr().out)
        assert code == EXIT_ISSUES
        assert payload["valid"] is False
        assert payload["issue_count"] >= 2

    def test_text_report_contains_health_and_issue(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        source = tmp_path / "bad.srt"
        source.write_text(SRT_BAD, encoding="utf-8")
        assert run_command(parse_args("validate", str(source))) == EXIT_ISSUES
        output = capsys.readouterr().out
        assert "Health score:" in output
        assert "Issues:" in output

    def test_preset_can_be_overridden(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        source = tmp_path / "clean.srt"
        source.write_text(SRT_ONE, encoding="utf-8")
        args = parse_args(
            "validate",
            str(source),
            "--preset",
            "netflix",
            "--max-cps",
            "100",
            "--json",
        )
        run_command(args)
        assert "health" in json.loads(capsys.readouterr().out)

    def test_inverted_duration_range_is_rejected(self, source: Path) -> None:
        args = parse_args(
            "validate",
            str(source),
            "--min-duration",
            "5",
            "--max-duration",
            "1",
        )
        with pytest.raises(ValueError, match="cannot exceed"):
            run_command(args)


class TestMain:
    def test_success_raises_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["info"])
        assert exc.value.code == EXIT_OK
        assert "subcue" in capsys.readouterr().out

    def test_missing_file_becomes_concise_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        missing = tmp_path / "missing.srt"
        with pytest.raises(SystemExit) as exc:
            main(["import", str(missing)])
        captured = capsys.readouterr()
        assert exc.value.code == EXIT_ERROR
        assert "file not found" in captured.err
        assert "Traceback" not in captured.err

    def test_empty_stdin_is_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(sys, "stdin", __import__("io").StringIO(""))
        with pytest.raises(SystemExit) as exc:
            main(["import", "-"])
        assert exc.value.code == EXIT_ERROR
        assert "stdin is empty" in capsys.readouterr().err
