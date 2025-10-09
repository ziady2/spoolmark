"""Tests for plugin."""

from __future__ import annotations

import pytest

from subcue.errors import DuplicateError, NotFoundError
from subcue.plugin import (
    PluginFunc,
    clear,
    get_plugin,
    list_plugins,
    register,
    run_pipeline,
    run_plugin,
    unregister,
)


class TestPluginFunc:
    def test_exists(self):
        assert PluginFunc is not None


class Test_clear:
    def test_callable(self):
        assert callable(clear)


class Test_get_plugin:
    def test_callable(self):
        assert callable(get_plugin)

    def test_missing_plugin_raises_domain_error(self):
        clear()
        with pytest.raises(NotFoundError) as exc_info:
            get_plugin("missing")
        assert exc_info.value.kind == "plugin"
        assert exc_info.value.identifier == "missing"


class Test_list_plugins:
    def test_callable(self):
        assert callable(list_plugins)


class Test_register:
    def test_callable(self):
        assert callable(register)

    def test_duplicate_plugin_raises_domain_error(self):
        clear()
        register("same", lambda data: data)
        try:
            with pytest.raises(DuplicateError) as exc_info:
                register("same", lambda data: data)
            assert exc_info.value.kind == "plugin"
            assert exc_info.value.identifier == "same"
        finally:
            clear()


class Test_run_pipeline:
    def test_callable(self):
        assert callable(run_pipeline)


class Test_run_plugin:
    def test_callable(self):
        assert callable(run_plugin)


class Test_unregister:
    def test_callable(self):
        assert callable(unregister)

    def test_missing_plugin_raises_domain_error(self):
        clear()
        with pytest.raises(NotFoundError):
            unregister("missing")
