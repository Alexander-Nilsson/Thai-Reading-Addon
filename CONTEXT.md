# Chinese Reading — domain glossary

## Reading Generation

The core feature: lookup Chinese text in the dictionary DB, produce tone-coloured readings (pinyin/bopomofo/jyutping), and optionally add simplified/traditional character variants.

- **Reading** — the phonetic transcription of a Chinese character or word (pinyin, bopomofo, or jyutping), including tone marks/numbers.
- **Segment and lookup** — the algorithm that splits Chinese text into dictionary-lookupable tokens via greedy lookahead then fallback to single characters.
- **Active Field** — an entry in the addon config specifying which profile/note-type/card-type/field/side gets which display type and reading type.

## Configuration

- **AddonConfig** — frozen dataclass wrapping the `config.json` dict. Typed properties for every setting.
- **ConfigMutation** — the module (deep, proposed) that validates, transforms, and persists configuration deltas. Owns all config logic. Sits behind a seam from `SettingsGui`.
- **ConfigDelta** — a frozen typed dataclass where every config key is an `Optional` field. `SettingsGui` extracts widget state into a `ConfigDelta` and passes it to `ConfigMutation`.
- **ModelCatalog** — a Protocol (seam) providing typed queries over Anki note types, card types, and fields per profile. Replaces the leaky `colArray` global dict. `LiveModelCatalog` is the production adapter; `StubModelCatalog` is the test adapter.

## Template Injection

- **CSSJSHandler** — reads JS files from `js/`, injects/removes CSS, JS, and wrapper elements into Anki card templates.
- **TemplateInjector** — the proposed deep module consolidating `CSSJSHandler`'s 27 inject/remove/edit methods into `inject(component, template)` and `remove(component, template)`.

## Cross-cutting

- **AnkiServices** — a Protocol (seam) for `mw.col`, `mw.pm`, `mw.app`, `mw.progress` operations. `LiveAnkiServices` is the production adapter.
- **JsRegistry** — file-system cache for JS files in `js/`.
- **DictDB** — SQLite wrapper for `db/chinese_dict.sqlite`.
- **Seam** — a place behaviour can be altered without editing in place (from LANGUAGE.md). Used to describe the boundary between GUI and config logic.
