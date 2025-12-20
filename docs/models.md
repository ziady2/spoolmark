# Data Model

## Core classes

- **Cue** — a single timed subtitle entry (index, start, end, text, speaker, style)
- **Track** — ordered sequence of Cues with metadata
- **Style** — font, color, alignment (ASS compatible)
- **Speaker** — voice attribution
- **DialogueLine** — speaker + cue pair
- **Project** — multi-track container
- **Marker** — scene/chapter marker
- **Metadata** — title, language, fps, encoding

## Serialisation

Every model supports `to_dict()`, `from_dict()`, and `copy()`.
