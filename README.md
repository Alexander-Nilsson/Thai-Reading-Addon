<h2 align="center">Thai Reading Addon</h2>

> An Anki add-on for Thai learners. Generates tone-coloured readings (RTGS/IPA) and injects CSS/JS into card templates.

## Features

- **Tone-coloured readings**: RTGS and IPA with 5 configurable Thai tone colours
- **Card template injection**: Auto-injects CSS and JavaScript into card templates for tone colouring
- **Active Fields system**: Configure which note types, card types, fields, and card sides get processed
- **Segment and lookup**: Greedy-lookahead tokenization for dictionary matching
- **Exportable configuration**: Supports profiles for different reading workflows

## Configuration

Access settings via **Tools → Thai Reading Settings** or through Anki's add-on config editor.

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
