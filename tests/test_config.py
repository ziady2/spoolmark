"""Tests for config."""

from __future__ import annotations

import json

import pytest

from subcue.config import Config, load_config, validate_config
from subcue.errors import ConfigError


class TestConfig:
    def test_default(self):
        cfg = Config()
        assert cfg.get("default_format") == "srt"

    def test_override(self):
        cfg = Config({"locale": "fr"})
        assert cfg.get("locale") == "fr"

    def test_getitem(self):
        cfg = Config()
        assert cfg["locale"] == "en"

    def test_missing_raises(self):
        with pytest.raises(ConfigError):
            Config()["nope"]

    def test_contains(self):
        cfg = Config()
        assert "locale" in cfg

    def test_to_dict(self):
        d = Config().to_dict()
        assert "default_fps" in d

    def test_with_override(self):
        cfg = Config()
        new = cfg.with_override("locale", "de")
        assert new.get("locale") == "de" and cfg.get("locale") == "en"

    def test_max_cps(self):
        assert Config().max_cps == 25.0

    def test_min_duration(self):
        assert Config().min_duration == 0.7

    def test_rejects_non_mapping_data_with_domain_error(self):
        with pytest.raises(ConfigError, match="JSON-style object"):
            Config([("locale", "fr")])  # type: ignore[arg-type]


class TestLoadConfig:
    def test_nonexistent(self, tmp_path):
        cfg = load_config(tmp_path / "nope.json")
        assert cfg.get("locale") == "en"

    def test_valid(self, tmp_path):
        p = tmp_path / "c.json"
        p.write_text(json.dumps({"locale": "ar"}))
        assert load_config(p).get("locale") == "ar"

    def test_bad_json(self, tmp_path):
        p = tmp_path / "b.json"
        p.write_text("{bad}")
        with pytest.raises(ConfigError):
            load_config(p)

    def test_bad_encoding_raises_domain_error(self, tmp_path):
        path = tmp_path / "bad-encoding.json"
        path.write_bytes(b"\xff")

        with pytest.raises(ConfigError, match="config_file"):
            load_config(path)

    @pytest.mark.parametrize("raw", ["[]", "null", "42", '"text"'])
    def test_rejects_non_object_json_with_domain_error(self, tmp_path, raw):
        path = tmp_path / "wrong-shape.json"
        path.write_text(raw)

        with pytest.raises(ConfigError, match="top-level JSON value must be an object"):
            load_config(path)


class TestValidateConfig:
    def test_valid(self):
        assert validate_config(Config()) == []

    def test_bad_format(self):
        assert len(validate_config(Config({"default_format": "pdf"}))) > 0

    @pytest.mark.parametrize(
        "data,key",
        [
            ({"default_fps": float("nan")}, "default_fps"),
            ({"default_fps": float("inf")}, "default_fps"),
            ({"default_fps": 10**1000}, "default_fps"),
            ({"max_cps": 0}, "max_cps"),
            ({"min_duration": -1}, "min_duration"),
            ({"max_duration": 0}, "max_duration"),
            ({"min_gap": -1}, "min_gap"),
            ({"line_length": 0}, "line_length"),
            ({"line_length": 42.5}, "line_length"),
            ({"max_lines": True}, "max_lines"),
            ({"color_output": "yes"}, "color_output"),
            ({"data_dir": ""}, "data_dir"),
            ({"locale": 123}, "locale"),
            ({"encoding": "not-a-real-codec"}, "encoding"),
        ],
    )
    def test_reports_invalid_schema_values(self, data, key):
        assert any(key in warning for warning in validate_config(Config(data)))

    def test_reports_inverted_duration_range_and_unknown_keys(self):
        warnings = validate_config(
            Config({"min_duration": 2.0, "max_duration": 1.0, "unexpected": True})
        )

        assert any("max_duration must be greater" in warning for warning in warnings)
        assert any("unknown configuration key 'unexpected'" in warning for warning in warnings)
