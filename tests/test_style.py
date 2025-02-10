"""Tests for style."""

from __future__ import annotations

import pytest

from subcue.errors import ValidationError
from subcue.style import Style


class TestStyle:
    def test_basic(self):
        s = Style("Default")
        assert s.name == "Default"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            Style("")

    def test_bad_font_size_raises(self):
        with pytest.raises(ValidationError):
            Style("X", font_size=0)

    def test_equality(self):
        assert Style("A") == Style("A")

    def test_to_dict(self):
        d = Style("X").to_dict()
        assert d["name"] == "X"

    def test_from_dict(self):
        s = Style.from_dict({"name": "Y", "font_size": 24})
        assert s.font_size == 24

    def test_copy(self):
        s = Style("X", bold=True)
        c = s.copy()
        assert c.bold is True

    def test_css(self):
        css = Style("X", bold=True).css()
        assert "bold" in css

    def test_alignment_label(self):
        s = Style("X", alignment=2)
        assert "bottom" in s.alignment_label()
