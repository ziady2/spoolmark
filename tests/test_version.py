"""Tests for version."""

from __future__ import annotations

import pytest

from subcue.version import (
    VERSION_INFO,
    __version__,
    build_user_agent,
    check_python_version,
    version_string,
    version_tuple,
)


class TestVersion:
    def test_version_is_string(self):
        assert isinstance(__version__, str)

    def test_format(self):
        parts = __version__.split(".")
        assert len(parts) == 3 and all(p.isdigit() for p in parts)

    def test_version_info(self):
        assert len(VERSION_INFO) == 3

    def test_version_string(self):
        assert "subcue" in version_string()

    def test_version_tuple(self):
        t = version_tuple()
        assert len(t) == 3

    def test_check_python(self):
        assert check_python_version((3, 9)) is True
        assert check_python_version((99, 0)) is False

    def test_user_agent(self):
        ua = build_user_agent()
        assert "subcue/" in ua

    @pytest.mark.parametrize("min_ver", [(3, 0), (3, 9), (2, 7)])
    def test_various_minimums(self, min_ver):
        assert isinstance(check_python_version(min_ver), bool)
