# Thai Reading — domain glossary

## Reading Generation

The core feature: lookup Thai text in the dictionary DB, produce readings (RTGS/IPA) with tone-colouring, and optionally add syllabified transcriptions.

- **Reading** — the phonetic transcription of a Thai word (RTGS or IPA), including tone numbers.
- **Segment and lookup** — the algorithm that splits Thai text into dictionary-lookupable tokens via greedy lookahead then fallback to single characters.
- **Active Field** — an entry in the addon config specifying which profile/note-type/card-type/field/side gets which display type and reading type.

## Thai Tones

Thai has 5 phonemic tones:
1. Mid (สามัญ) — no tone mark
2. Low (เอก)
3. Falling (โท)
4. High (ตรี)
5. Rising (จัตวา)

Each configurable with a hex colour in `ThaiTones`.

## Configuration

- **AddonConfig** — frozen dataclass wrapping the `config.json` dict. Typed properties for every setting.
- **ConfigMutation** — the module that validates, transforms, and persists configuration deltas. Owns all config logic. Sits behind a seam from `SettingsGui`.
- **ConfigDelta** — a frozen typed dataclass where every config key is an `Optional` field.
- **ModelCatalog** — a Protocol (seam) providing typed queries over Anki note types, card types, and fields per profile.

## Template Injection

- **ThaiCssJsHandler** — reads JS files from `js/`, injects/removes CSS, JS, and wrapper elements into Anki card templates.
- **TemplateInjector** — handles injection/removal of components with marker comments.

## Cross-cutting

- **AnkiServices** — a Protocol (seam) for `mw.col`, `mw.pm`, `mw.app`, `mw.progress` operations. `LiveAnkiServices` is the production adapter.
- **JsRegistry** — file-system cache for JS files in `js/`.
- **DictDB** — SQLite wrapper for `db/thai_dict.sqlite`.
- **Seam** — a place behaviour can be altered without editing in place.
