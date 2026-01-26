"""Example: run diagnostics on a subtitle track."""

from __future__ import annotations

from subcue.ascii_renderer import table_string
from subcue.cue import Cue
from subcue.diagnostic import health_score, issue_summary, run_diagnostics
from subcue.track import Track


def main() -> None:
    # Create a track with some issues
    cues = [
        Cue(1, 0.0, 0.3, "Too short!"),
        Cue(2, 0.5, 3.0, "This one overlaps."),
        Cue(3, 2.5, 5.0, "Overlap detected here."),
        Cue(4, 6.0, 7.0, "A" * 50 + "\n" + "B" * 50),
        Cue(5, 8.0, 15.0, "This subtitle stays way too long on screen."),
        Cue(6, 16.0, 19.0, "Normal subtitle."),
        Cue(7, 20.0, 22.0, "Another normal one."),
        Cue(8, 22.01, 24.0, "Tiny gap before this."),
    ]
    track = Track("Diagnostic Demo", cues=cues)

    # Run diagnostics
    issues = run_diagnostics(track)
    print(f"Found {len(issues)} issues:\n")
    for issue in issues:
        cue_label = "-" if issue["cue_index"] is None else str(issue["cue_index"])
        print(f"  [{issue['severity']:>7}] Cue {cue_label:>2}: {issue['message']}")

    # Health score
    print(f"\n{'-' * 40}")
    score = health_score(track)
    print(f"Health score: {score['score']}/100")
    print(f"  Errors: {score['errors']}")
    print(f"  Warnings: {score['warnings']}")
    print(f"  Info: {score['info']}")

    # Issue summary
    print(f"\n{'=' * 40}")
    print("Issue summary:")
    summary = issue_summary(track)
    columns = ["issue_type", "count", "severity"]
    rows = [[str(item[column]) for column in columns] for item in summary]
    print(table_string(columns, rows))


if __name__ == "__main__":
    main()
