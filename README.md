<div align="center">

# Thai Reading Addon

An Anki add-on for Thai learners — generates tone-coloured readings (RTGS / IPA / Paiboon) and injects CSS/JS into card templates.

[![AnkiWeb](https://img.shields.io/badge/AnkiWeb-2062807229-blue?style=flat-square)](https://ankiweb.net/shared/info/2062807229)
[![License](https://img.shields.io/badge/license-AGPLv3-green?style=flat-square)](LICENSE)

</div>

---

## Features

- **Tone-coloured readings** — RTGS, IPA, and Paiboon with 5 configurable Thai tone colours
- **Template injection** — Auto-injects CSS and JavaScript into card templates for tone colouring
- **Active Fields system** — Configure which note types, card types, fields, and sides get processed
- **Segment & lookup** — Greedy-lookahead tokenization for dictionary matching

---

## Reading Systems

### IPA (International Phonetic Alphabet)

```
/tɕʰan˩˩˦ tɕʰɔːp̚˥˩ kin˧ kʰaːw˥˩ pʰat̚˨˩ maːk̚˥˩ kʰrap̚˦˥/
```

Precise phonetic transcription with tone letters.

### Paiboon (learner-friendly)

```
chǎn chɔ̂ɔp gin kâao pàt mâak kráp
```

Tone diacritics on vowels, doubled for length.


### RTGS Tone Display

The addon's dictionary stores RTGS readings in a digit-suffix format (`sa2 wat2 di1`), where each digit maps to a Thai tone class. Readings can be displayed in two styles:

| Style | Example | Description |
|---|---|---|
| `marks` (default) | `chǎn chóp kin khâao phàt mâak khráp` | Digits replaced with conventional tone diacritics on the syllable's vowel |
| `numbers` | `chan5 chop3 kin1 khao3 phat2 mak3 khrap4` | Raw digit suffix per syllable, as stored in the dictionary |

Tone colours always work from the underlying tone number regardless of which reading system or display style is selected. Switch between Reading systems and styles via **Tools → Thai Reading Settings**.

---

## Visual Reference

A demo page showing all display types, reading types, and tone colours is available in [`demo/index.html`](demo/index.html).

![Display options preview](demo/readings-screenshot.png)

---

## Configuration

Access settings via **Tools → Thai Reading Settings** or through Anki's add-on config editor.

| Key | Type | Default | Description |
|---|---|---|---|
| `ReadingType` | `"rtgs"` \| `"ipa"` \| `"phonetics"` | `"rtgs"` | Default reading system |
| `FontSize` | `int` (1–200) | `75` | Reading font size as % of base text |
| `ThaiTones` | `[str; 5]` | `["#78716C","#0F766E","#B91C1C","#D97706","#7C3AED"]` | Colours for tones 1–5 (Mid, Low, Falling, High, Rising) |
| `RtgsToneStyle` | `"marks"` \| `"numbers"` | `"marks"` | Tone marks on vowels (`sà`) or digit suffix (`sa2`) |
| `AutoCssJsGeneration` | `bool` | `true` | Auto-inject CSS/JS into card templates |
| `ShortcutKey` | `str` | `"F9"` | Keyboard shortcut for toggle reading (set `""` to disable) |
| `Profiles` | `[str]` | `["all"]` | Anki profiles the addon is active on |
| `UseFileReferences` | `bool` | `false` | Write CSS/JS as standalone files in collection.media |
| `ActiveFields` | `[str]` | `[]` | Entries: `display;profile;noteType;cardType;field;side;readingType` |

---

## Dependencies

### Pronunciation dictionary

These populate `db/thai_dict.sqlite`:

| Dependency | Role |
|---|---|
| [`thaiphon`](https://pypi.org/project/thaiphon/) ≥0.6.0 | Thai phonetic transcription engine — RTGS and IPA rendering, syllable analysis, tone detection |
| [`thaiphon-data-volubilis`](https://pypi.org/project/thaiphon-data-volubilis/) ≥0.2.0 | ~84k word Thai pronunciation lexicon (optional but recommended) |

Run `uv run python db/populate_dict.py` to build the dictionary.

### Runtime

No additional pip dependencies. Uses `PyQt6`, `aqt`, and `anki` provided by the Anki environment.

### Development tooling

| Tool | Purpose |
|---|---|
| `ruff` | Linter and formatter |
| `pytest` | Unit test runner |
| `pytest-anki2` | Integration test fixtures |
| `ty` | Static type checker |

---

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

---

## License

GNU AGPLv3 — see [LICENSE](LICENSE).
