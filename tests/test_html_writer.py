"""Tests for html_writer."""

from __future__ import annotations

from subcue.html_writer import (
    Sequence,
    escape_html,
    render_cue_list,
    render_report_table,
    render_track_preview,
    wrap_html_page,
)


class Test_Sequence:
    def test_callable(self):
        assert callable(Sequence)


class Test_escape_html:
    def test_callable(self):
        assert callable(escape_html)


class Test_render_cue_list:
    def test_callable(self):
        assert callable(render_cue_list)


class Test_render_report_table:
    def test_callable(self):
        assert callable(render_report_table)


class Test_render_track_preview:
    def test_callable(self):
        assert callable(render_track_preview)


class Test_wrap_html_page:
    def test_callable(self):
        assert callable(wrap_html_page)
