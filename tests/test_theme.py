"""Tests for theme."""

from __future__ import annotations

from subcue.theme import Theme, get_theme, register_theme


class TestTheme:
    def test_create(self):
        assert Theme is not None

    def test_as_dict_exists(self):
        assert hasattr(Theme, "as_dict")

    def test_css_variables_exists(self):
        assert hasattr(Theme, "css_variables")


class Test_get_theme:
    def test_callable(self):
        assert callable(get_theme)


class Test_register_theme:
    def test_callable(self):
        assert callable(register_theme)
