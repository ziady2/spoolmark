"""Tests for svg_renderer."""

from __future__ import annotations

from subcue.cue import Cue
from subcue.svg_renderer import Sequence, escape_html, svg_bar_chart, svg_line_chart, svg_timeline
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


class Test_escape_html:
    def test_callable(self):
        assert callable(escape_html)


class Test_svg_bar_chart:
    def test_callable(self):
        assert callable(svg_bar_chart)


class Test_svg_line_chart:
    def test_callable(self):
        assert callable(svg_line_chart)


class Test_svg_timeline:
    def test_callable(self):
        assert callable(svg_timeline)
