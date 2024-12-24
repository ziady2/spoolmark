"""Tests for errors."""

from __future__ import annotations

from subcue.errors import (
    ConfigError,
    DuplicateError,
    NotFoundError,
    OverlapError,
    ParseError,
    SubcueError,
    TimecodeError,
    ValidationError,
)


class TestSubcueError:
    def test_basic(self):
        e = SubcueError("boom")
        assert str(e) == "boom"

    def test_empty(self):
        assert "SubcueError" in str(SubcueError())

    def test_repr(self):
        assert "SubcueError" in repr(SubcueError("x"))

    def test_is_exception(self):
        assert issubclass(SubcueError, Exception)


class TestParseError:
    def test_with_line(self):
        e = ParseError("bad", line=5)
        assert "line 5" in str(e) and e.line == 5

    def test_without_line(self):
        e = ParseError("oops")
        assert e.line is None

    def test_inherits(self):
        assert issubclass(ParseError, SubcueError)


class TestValidationError:
    def test_fields(self):
        e = ValidationError("name", "too short")
        assert e.field == "name" and e.reason == "too short"


class TestTimecodeError:
    def test_basic(self):
        e = TimecodeError("bad:tc")
        assert "bad:tc" in str(e)

    def test_with_detail(self):
        e = TimecodeError("x", "missing hours")
        assert "missing hours" in str(e)


class TestOverlapError:
    def test_basic(self):
        e = OverlapError(1, 2)
        assert "1" in str(e) and "2" in str(e)


class TestNotFoundError:
    def test_basic(self):
        e = NotFoundError("cue", "42")
        assert e.kind == "cue"


class TestDuplicateError:
    def test_basic(self):
        e = DuplicateError("track", "en")
        assert "en" in str(e)


class TestConfigError:
    def test_basic(self):
        e = ConfigError("fps")
        assert "fps" in str(e)
