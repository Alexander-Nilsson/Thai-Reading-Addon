from dataclasses import dataclass, field

_DISPLAY_OPTIONS = [
    "hover",
    "coloredhover",
    "thai",
    "coloredthai",
    "reading",
    "coloredreading",
    "thaithai",
    "coloredthaithai",
]

_READING_OPTIONS = ["rtgs", "ipa"]


@dataclass(frozen=True)
class ActiveField:
    display_type: str
    profile: str
    note_type: str
    card_type: str
    field: str
    side: str
    reading_type: str = "default"

    @property
    def is_valid_syntax(self) -> bool:
        return self.display_type.lower() in _DISPLAY_OPTIONS


@dataclass(frozen=True)
class AddonConfig:
    _raw: dict = field(repr=False)

    @property
    def profiles(self) -> list[str]:
        return self._raw.get("Profiles", ["all"])

    @property
    def reading_type(self) -> str:
        return self._raw.get("ReadingType", "rtgs")

    @property
    def auto_css_js_generation(self) -> bool:
        return self._raw.get("AutoCssJsGeneration", True)

    @property
    def font_size(self) -> int:
        return self._raw.get("FontSize", 75)

    @property
    def thai_tones(self) -> list[str]:
        return self._raw.get("ThaiTones", ["#78716C", "#0F766E", "#B91C1C", "#D97706", "#7C3AED"])

    @property
    def rtgs_tone_style(self) -> str:
        return self._raw.get("RtgsToneStyle", "marks")

    @property
    def use_file_references(self) -> bool:
        return self._raw.get("UseFileReferences", False)

    @property
    def active_fields(self) -> list[str]:
        return self._raw.get("ActiveFields", [])

    def __getitem__(self, key):
        return self._raw[key]

    def get(self, key, default=None):
        return self._raw.get(key, default)

    def keys(self):
        return self._raw.keys()

    @classmethod
    def from_anki(cls, mw, addon_module_name: str):
        raw = mw.addonManager.getConfig(addon_module_name) or {}
        return cls(_raw=raw)


def parse_active_field(raw: str) -> ActiveField:
    parts = raw.split(";")
    if (len(parts) != 6 and len(parts) != 7) or "" in parts:
        raise ValueError(f'invalid syntax: "{raw}"')
    display_type = parts[0].lower()
    if display_type not in _DISPLAY_OPTIONS:
        raise ValueError(f'invalid display type: "{parts[0]}"')
    reading_type = "default"
    if len(parts) == 7:
        reading_type = parts[6].lower()
        if reading_type not in _READING_OPTIONS and reading_type != "default":
            raise ValueError(f'invalid reading type: "{parts[6]}"')
    return ActiveField(
        display_type=display_type,
        profile=parts[1],
        note_type=parts[2],
        card_type=parts[3],
        field=parts[4],
        side=parts[5],
        reading_type=reading_type,
    )


def serialize_active_field(af: ActiveField) -> str:
    return f"{af.display_type};{af.profile};{af.note_type};{af.card_type};{af.field};{af.side};{af.reading_type}"
