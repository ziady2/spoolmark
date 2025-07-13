"""Tests for color."""

from __future__ import annotations

from subcue.color import Color


class TestColor:
    def test_create(self):
        assert Color is not None

    def test_contrast_text_exists(self):
        assert hasattr(Color, "contrast_text")

    def test_darken_exists(self):
        assert hasattr(Color, "darken")

    def test_from_hex_exists(self):
        assert hasattr(Color, "from_hex")

    def test_gradient_exists(self):
        assert hasattr(Color, "gradient")

    def test_lighten_exists(self):
        assert hasattr(Color, "lighten")
