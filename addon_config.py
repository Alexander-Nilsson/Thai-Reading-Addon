from dataclasses import dataclass, field


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
