# Contributing

## Setup

```bash
git clone https://github.com/ziady2/spoolmark.git
cd subcue
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest -q
pytest --cov=subcue --cov-report=term-missing
```

## Code Style

- `from __future__ import annotations` in every module
- Relative imports only
- Type hints on all public APIs
- Docstrings on all public classes and functions
- Max line length: 100
- Run `ruff check src tests examples scripts` before committing

## Adding a Report

Reports should return `list[dict]` with consistent keys unless a documented
nested dictionary is more suitable.
Never mutate input data. Support `top` filter where applicable.

## Adding a New Parser

Parser modules must follow this contract:

1. Accept decoded text and return a `Track`.
2. Strip a leading BOM and normalise line endings where necessary.
3. Raise `ParseError`, including a line number when one is available.
4. Provide a `parse_*_file()` wrapper for direct UTF-8 file access. New
   application workflows should use `subcue.io.load_track` for encoding
   detection and format dispatch.

```python
def parse_xyz_text(text: str, *, name: str = 'XYZ Track') -> Track:
    text = strip_bom(text).strip()
    if not text:
        raise ParseError('empty input')
    cues = parse_xyz_cues(text)
    if not cues:
        raise ParseError('no valid cues found')
    return Track(name, cues=cues)
```

## Adding a New Report

Reports should return `list[dict]` with consistent keys:

```python
def my_report(track: Track, *, top: int = 0) -> list[dict]:
    results = []
    for cue in track.cues:
        results.append({
            'index': cue.index,
            'value': cue.cps,
            'status': 'ok' if cue.cps <= 20 else 'warn',
        })
    results.sort(key=lambda r: r['value'], reverse=True)
    if top > 0:
        results = results[:top]
    return results
```

## Commit Message Format

Use conventional commit prefixes:
- feat: new feature
- fix: bug fix
- test: test additions or fixes
- docs: documentation
- refactor: code restructuring
- style: formatting only
- perf: performance improvement
- chore: build/config changes

## Release Checklist

1. All tests pass (pytest -q)
2. Coverage >= 75 percent
3. ruff check passes
4. CHANGELOG updated
5. Version bumped in version.py and pyproject.toml
6. Git tag created
