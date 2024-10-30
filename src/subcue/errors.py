"""Exception hierarchy for subcue."""

from __future__ import annotations


class SubcueError(Exception):
    """Base exception for all subcue errors."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message or self.__class__.__name__

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        return f"{cls}({self.message!r})" if self.message else f"{cls}()"


class ParseError(SubcueError):
    """Raised when a subtitle file cannot be parsed."""

    def __init__(self, message: str, *, line: int | None = None) -> None:
        self.line = line
        prefix = f"line {line}: " if line is not None else ""
        super().__init__(f"{prefix}{message}")


class ValidationError(SubcueError):
    """Raised when data fails validation."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


class FormatError(SubcueError):
    """Raised when an output format cannot be produced."""


class TimecodeError(SubcueError):
    """Raised when a timecode string is malformed."""

    def __init__(self, raw: str, detail: str = "") -> None:
        self.raw = raw
        msg = f"bad timecode {raw!r}"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


class OverlapError(SubcueError):
    """Raised when cues overlap and that is not allowed."""

    def __init__(self, index_a: int, index_b: int) -> None:
        self.index_a = index_a
        self.index_b = index_b
        super().__init__(f"cues {index_a} and {index_b} overlap")


class NotFoundError(SubcueError):
    """Raised when a requested item does not exist."""

    def __init__(self, kind: str, identifier: str) -> None:
        self.kind = kind
        self.identifier = identifier
        super().__init__(f"{kind} not found: {identifier!r}")


class DuplicateError(SubcueError):
    """Raised when a uniqueness constraint is violated."""

    def __init__(self, kind: str, identifier: str) -> None:
        self.kind = kind
        self.identifier = identifier
        super().__init__(f"duplicate {kind}: {identifier!r}")


class ConfigError(SubcueError):
    """Raised when a configuration value is invalid."""

    def __init__(self, key: str, reason: str = "invalid value") -> None:
        self.key = key
        super().__init__(f"config[{key!r}]: {reason}")
