from dataclasses import dataclass, field


_DISPLAY_OPTIONS = [
    "hover",
    "coloredhover",
    "hanzi",
    "coloredhanzi",
    "reading",
    "coloredreading",
    "hanzireading",
    "coloredhanzireading",
]

_READING_OPTIONS = ["pinyin", "bopomofo", "jyutping"]


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
    def bopomofo_tones_to_number(self) -> bool:
        return self._raw.get("BopomofoTonesToNumber", True)

    @property
    def hanzi_conversion(self) -> str:
        return self._raw.get("hanziConversion", "None")

    @property
    def reading_conversion(self) -> str:
        return self._raw.get("readingConversion", "None")

    @property
    def auto_css_js_generation(self) -> bool:
        return self._raw.get("AutoCssJsGeneration", True)

    @property
    def reading_type(self) -> str:
        return self._raw.get("ReadingType", "pinyin")

    @property
    def simplified_field(self) -> str:
        return self._raw.get("SimplifiedField", "Simplified;overwrite")

    @property
    def traditional_field(self) -> str:
        return self._raw.get("TraditionalField", "Traditional;overwrite")

    @property
    def simp_trad_field(self) -> str:
        return self._raw.get("SimpTradField", "Traditional,Variant;overwrite")

    @property
    def traditional_icons(self) -> bool:
        return self._raw.get("traditionalIcons", False)

    @property
    def font_size(self) -> int:
        return self._raw.get("FontSize", 75)

    @property
    def cantonese_tones(self) -> list[str]:
        return self._raw.get("CantoneseTones123456", ["#E60000", "#E68A00", "#00802B", "#005CE6", "#AC00E6", "gray"])

    @property
    def mandarin_tones(self) -> list[str]:
        return self._raw.get("MandarinTones12345", ["#E60000", "#E68A00", "#00802B", "#005CE6", "gray"])

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
    def from_anki(cls, mw):
        return cls(_raw=mw.addonManager.getConfig(__name__))


def parse_active_field(raw: str) -> ActiveField | str:
    parts = raw.split(";")
    if (len(parts) != 6 and len(parts) != 7) or "" in parts:
        return f'invalid syntax: "{raw}"'
    display_type = parts[0].lower()
    if display_type not in _DISPLAY_OPTIONS:
        return f'invalid display type: "{parts[0]}"'
    reading_type = "default"
    if len(parts) == 7:
        reading_type = parts[6].lower()
        if reading_type not in _READING_OPTIONS and reading_type != "default":
            return f'invalid reading type: "{parts[6]}"'
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
