"""Tests for table."""

from __future__ import annotations

from subcue.table import (
    Sequence,
    TableBuilder,
    format_table,
    pad_left,
    pad_right,
    pivot_table,
    transpose,
)


class TestTableBuilder:
    def test_exists(self):
        assert TableBuilder is not None


class Test_Sequence:
    def test_callable(self):
        assert callable(Sequence)


class Test_format_table:
    def test_callable(self):
        assert callable(format_table)


class Test_pad_left:
    def test_callable(self):
        assert callable(pad_left)


class Test_pad_right:
    def test_callable(self):
        assert callable(pad_right)


class Test_pivot_table:
    def test_callable(self):
        assert callable(pivot_table)


class Test_transpose:
    def test_callable(self):
        assert callable(transpose)
