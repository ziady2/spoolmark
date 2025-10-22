"""Tests for validation."""

from __future__ import annotations

import pytest

from subcue.errors import TimecodeError, ValidationError
from subcue.validation import (
    parse_timecode,
    require_non_empty,
    require_positive,
    sanitise_string,
    validate_cue_data,
    validate_timecode,
    validate_track_data,
)


class Test_parse_timecode:
    def test_callable(self):
        assert callable(parse_timecode)


class Test_require_non_empty:
    def test_callable(self):
        assert callable(require_non_empty)

    def test_raises_validation_error_with_field(self):
        with pytest.raises(ValidationError) as exc_info:
            require_non_empty("  ", "title")
        assert exc_info.value.field == "title"


class Test_require_positive:
    def test_callable(self):
        assert callable(require_positive)

    def test_raises_validation_error_with_field(self):
        with pytest.raises(ValidationError) as exc_info:
            require_positive(0, "duration")
        assert exc_info.value.field == "duration"

    @pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
    def test_rejects_non_finite_and_boolean_values(self, value):
        with pytest.raises(ValidationError):
            require_positive(value)


class Test_sanitise_string:
    def test_callable(self):
        assert callable(sanitise_string)


class Test_validate_cue_data:
    def test_callable(self):
        assert callable(validate_cue_data)

    @pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
    def test_rejects_invalid_numeric_values(self, value):
        assert validate_cue_data({"start": value, "end": 2, "text": "x"})


class Test_validate_timecode:
    def test_callable(self):
        assert callable(validate_timecode)

    def test_invalid_value_raises_timecode_error_for_raw_input(self):
        with pytest.raises(TimecodeError) as exc_info:
            validate_timecode("not-a-time")
        assert exc_info.value.raw == "not-a-time"


class Test_validate_track_data:
    def test_callable(self):
        assert callable(validate_track_data)
