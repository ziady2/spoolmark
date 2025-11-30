# Contributing

## Setup

```bash
git clone https://github.com/ziady2/subcue.git
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
- Run `ruff check src tests` before committing

## Adding a Report

Reports must return `List[dict]` with consistent keys.
Never mutate input data. Support `top` filter where applicable.
