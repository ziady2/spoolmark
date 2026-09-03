# subcue

> Subtitle processing toolkit — parse, analyse and convert SRT, VTT and ASS caption files.

[![tests](https://github.com/ziady2/subcue/actions/workflows/tests.yml/badge.svg)](https://github.com/ziady2/subcue/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Features

- **Parse** SubRip (`.srt`), WebVTT (`.vtt`), ASS/SSA (`.ass`), JSON, and plain-text subtitles
- **Characters-per-second** (CPS) analysis for readability checks
- **Overlap & gap detection** across cue timelines
- **Speaker attribution** and dialogue turn analysis
- **Time shifting & scaling** for frame-rate conversions
- **12 built-in reports**: timing, CPS, overlaps, gaps, words, speakers, duration, read-speed, sync, conformance, styles, density
- **Multiple exports**: HTML preview, SVG timeline, ASCII tables, CSV, JSON
- **Zero dependencies** — stdlib only

## Quick Start

```bash
pip install -e ".[dev]"

# parse an SRT file
subcue import movie.srt

# analyse characters-per-second
subcue analyze cps --top 10

# shift timecodes by 2.5 seconds
subcue shift 2.5 movie.srt

# export as WebVTT
subcue export -f vtt -o movie.vtt

# validate against Netflix guidelines
subcue validate movie.srt

# merge multiple files
subcue merge english.srt french.srt
```

## Installation

```bash
git clone https://github.com/ziady2/subcue.git
cd subcue
pip install -e ".[dev]"
```

## Reports

| Report        | Description                              |
|---------------|------------------------------------------|
| `timing`      | Duration statistics per cue              |
| `cps`         | Characters-per-second analysis           |
| `overlap`     | Detect overlapping cues                  |
| `gaps`        | Gap analysis between cues                |
| `words`       | Word and character frequency             |
| `speakers`    | Speaker distribution                     |
| `duration`    | Cue duration distribution                |
| `readspeed`   | Reading speed conformance                |
| `sync`        | Sync validation                          |
| `conformance` | Standards conformance (Netflix, BBC)     |
| `styles`      | Style usage analysis                     |
| `density`     | Subtitle density over time               |

## Running Tests

```bash
pytest -q
pytest --cov=subcue
make test
```

## License

MIT — see [LICENSE](LICENSE).

## Documentation

- [Tutorial](docs/tutorial.md) — Step-by-step getting started guide
- [API Reference](docs/api.md) — Complete function and class reference
- [Subtitle Formats](docs/formats.md) — Supported file formats
- [Reports](docs/reports.md) — Available analysis reports
- [Conformance Presets](docs/presets.md) — Industry standard guidelines
- [CPS & Timing Guide](docs/timing.md) — Understanding readability metrics
- [Architecture](docs/architecture.md) — Internal design overview
- [Glossary](docs/glossary.md) — Subtitle terminology
- [FAQ](docs/faq.md) — Frequently asked questions
- [Contributing](docs/contributing.md) — Development setup and guidelines

## Acknowledgements

This project was built as a learning exercise in subtitle processing
and Python packaging. It uses only the Python standard library and
follows modern Python best practices including type hints, docstrings,
and comprehensive test coverage.

### Authors

- **Ziad Yasser** — [yziad845@gmail.com](mailto:yziad845@gmail.com)

### Contributors

Contributions welcome! See [Contributing](docs/contributing.md) for details.
