"""Tests for ascii_renderer."""

from __future__ import annotations

from subcue.ascii_renderer import (
    Sequence,
    bar,
    box,
    horizontal_bar_chart,
    progress_bar,
    sparkline,
    table_string,
)
from subcue.cue import Cue
from subcue.track import Track


def _track():
    return Track(
        "T",
        cues=[
            Cue(1, 0, 2, "Hello world", speaker="A"),
            Cue(2, 3, 6, "Second subtitle here", speaker="B"),
            Cue(3, 7, 8, "Short one", speaker="A"),
        ],
    )


class Test_Sequence:
    def test_callable(self):
        assert callable(Sequence)


class Test_bar:
    def test_callable(self):
        assert callable(bar)


class Test_box:
    def test_callable(self):
        assert callable(box)


class Test_horizontal_bar_chart:
    def test_callable(self):
        assert callable(horizontal_bar_chart)


class Test_progress_bar:
    def test_callable(self):
        assert callable(progress_bar)


class Test_sparkline:
    def test_callable(self):
        assert callable(sparkline)


class Test_table_string:
    def test_callable(self):
        assert callable(table_string)
