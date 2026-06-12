<h2 align="center">Chinese Reading Addon</h2>

<p align="center">
<a title="Rate on AnkiWeb" href="https://ankiweb.net/shared/info/1051095155"><img src="https://glutanimate.com/logos/ankiweb-rate.svg"></a>
<a title="License: GNU AGPLv3" href="LICENSE"><img src="https://img.shields.io/badge/license-GNU AGPLv3-green.svg"></a>
<br>

> An Anki add-on for Chinese learners. Generates tone-coloured readings (pinyin, bopomofo, jyutping), simplified/traditional variants, and injects CSS/JS into card templates.

---

## Active Fields

Configure which note types, card types, fields, and card sides get processed via the **Active Fields** tab in add-on settings.

Each entry is a semicolon-delimited string:

```
display_type;profile;note_type;card_type;field;side;reading_type
```

### Card type: `All`

When set to `All`, the entry applies to every card template of the given note type. This removes the need to create one entry per card type when the same field should be processed identically across all cards.

### Default hanzi wrapping

Fields that have an ActiveFields entry on at least one side will automatically get a default `hanzi` wrapper on their unconfigured sides. This means configuring a field for the **back** only will still get it wrapped as hanzi on the **front**, and vice versa.

Fields with **no** ActiveFields entry at all are left completely untouched — no wrappers are added, no JavaScript is injected for them. This prevents non-Chinese fields (Sound, Image, Keyword, etc.) from being unnecessarily processed.

### File references mode

When enabled (via the Options tab), CSS and JavaScript are written to `collection.media/` as standalone files and referenced via `<link>` and `<script src>` tags instead of being inlined into card templates. This keeps card templates smaller and avoids issues with Anki's inline script handling.
