"""Tests for presets."""

from __future__ import annotations

import pytest

from subcue.errors import NotFoundError
from subcue.presets import broadcast_preset, get_preset, list_presets, netflix_preset, web_preset


class Test_broadcast_preset:
    def test_callable(self):
        assert callable(broadcast_preset)


class Test_get_preset:
    def test_callable(self):
        assert callable(get_preset)

    def test_unknown_preset_raises_domain_error(self):
        with pytest.raises(NotFoundError) as exc_info:
            get_preset("cinema")
        assert exc_info.value.kind == "preset"
        assert exc_info.value.identifier == "cinema"


class Test_list_presets:
    def test_callable(self):
        assert callable(list_presets)


class Test_netflix_preset:
    def test_callable(self):
        assert callable(netflix_preset)


class Test_web_preset:
    def test_callable(self):
        assert callable(web_preset)
