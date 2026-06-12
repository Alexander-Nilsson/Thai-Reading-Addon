<h2 align="center">Chinese Reading Addon</h2>

<p align="center">
<a title="Rate on AnkiWeb" href="https://ankiweb.net/shared/info/1051095155"><img src="https://glutanimate.com/logos/ankiweb-rate.svg"></a>
<a title="License: GNU AGPLv3" href="LICENSE"><img src="https://img.shields.io/badge/license-GNU AGPLv3-green.svg"></a>
<br>

> An Anki add-on for Chinese learners. Generates tone-coloured readings (pinyin, bopomofo, jyutping), simplified/traditional variants, and injects CSS/JS into card templates.

---

## Features

- **Tone-coloured readings**: Pinyin, Bopomofo, and Jyutping with configurable tone colours
- **Simplified/Traditional variants**: Auto-generate character variants via the browser
- **Card template injection**: Auto-injects CSS and JavaScript into card templates for tone colouring
- **Active Fields system**: Configure which note types, card types, fields, and card sides get processed
- **Masked Hanzi mode**: Display readings while hiding the original characters
- **Exportable configuration**: Supports profiles for different reading workflows

## Configuration

Access settings via **Tools → Chinese Reading Settings** or through Anki's add-on config editor.

### Active Fields

Configure processing rules per note type/card type/field/side via the **Active Fields** tab. Each entry is a semicolon-delimited string:

```
display_type;profile;note_type;card_type;field;side;reading_type
```

- `display_type`: `hanzi`, `reading`, or `masked`
- `profile`: profile name or `all`
- `note_type`, `card_type`, `field`: target identifiers (use `All` for wildcard)
- `side`: `front` or `back`
- `reading_type`: `pinyin`, `bopomofo`, or `jyutping`

Fields with an ActiveFields entry on at least one side get a default `hanzi` wrapper on the other side. Fields with no entry are left untouched.

### File References Mode

When enabled, CSS/JS are written to `collection.media/` as standalone files referenced via `<link>`/`<script src>` instead of inline.

## Development

```bash
uv venv --python /usr/bin/python3.14 .venv
source .venv/bin/activate
uv sync

# Run checks
python dev.py lint        # ruff linter
python dev.py typecheck   # ty type checker
python dev.py test-unit   # fast unit tests (no Anki)
python dev.py test        # full test suite (needs Anki)
python dev.py build       # .ankiaddon package
python dev.py ci          # full CI pipeline
```

See [AGENTS.md](AGENTS.md) for architecture details and [docs/](docs/) for ADRs and testing docs.

## License

GNU AGPLv3 — see [LICENSE](LICENSE).
