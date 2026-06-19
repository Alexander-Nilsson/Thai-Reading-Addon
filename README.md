<h2 align="center">Thai Reading Addon</h2>

> An Anki add-on for Thai learners. Generates tone-coloured readings (RTGS/IPA) and injects CSS/JS into card templates.

## Features

- **Tone-coloured readings**: RTGS and IPA with 5 configurable Thai tone colours
- **Card template injection**: Auto-injects CSS and JavaScript into card templates for tone colouring
- **Active Fields system**: Configure which note types, card types, fields, and card sides get processed
- **Segment and lookup**: Greedy-lookahead tokenization for dictionary matching
- **Exportable configuration**: Supports profiles for different reading workflows

## Visual Reference

A demo page showing all display types, reading types, and tone colours is available in [`demo/index.html`](demo/index.html).

![Display options preview](demo/readings-screenshot.png)

## Configuration

Access settings via **Tools → Thai Reading Settings** or through Anki's add-on config editor.

## Dependencies

### Pronunciation dictionary (reading generation)

These are needed to build `db/thai_dict.sqlite` — the SQLite dictionary that powers all reading lookups:

| Dependency | Role |
|---|---|
| [`thaiphon`](https://pypi.org/project/thaiphon/) ≥0.6.0 | Thai phonetic transcription engine — RTGS and IPA rendering, syllable analysis, tone detection |
| [`thaiphon-data-volubilis`](https://pypi.org/project/thaiphon-data-volubilis/) ≥0.2.0 | ~84k word Thai pronunciation lexicon (optional but recommended for best coverage) |

Run `uv run python db/populate_dict.py` to populate the dictionary from these.

### Runtime

The addon runs inside Anki and has no additional pip dependencies at runtime. It uses PyQt6, `aqt`, and `anki` — all provided by the Anki environment. Bare `thaiphon` calls are only made during dictionary population, not during card review or editing.

### Development tooling

| Tool | Purpose |
|---|---|
| `ruff` | Linter and formatter |
| `pytest` | Unit test runner |
| `pytest-anki2` | Anki integration test fixtures |
| `ty` | Static type checker |

## Development

```bash
uv venv .venv
source .venv/bin/activate
uv sync

# Populate pronunciation dictionary
uv run python db/populate_dict.py

# Run checks
python dev.py lint        # ruff linter
python dev.py typecheck   # ty type checker
python dev.py test-unit   # fast unit tests (no Anki)
python dev.py test        # full test suite (needs Anki)
python dev.py build       # .ankiaddon package
python dev.py ci          # full CI pipeline
```

## License

GNU AGPLv3 — see [LICENSE](LICENSE).
