from config.config import AddonConfig


def test_defaults():
    cfg = AddonConfig(_raw={})
    assert cfg.profiles == ["all"]
    assert cfg.bopomofo_tones_to_number is True
    assert cfg.hanzi_conversion == "None"
    assert cfg.reading_conversion == "None"
    assert cfg.auto_css_js_generation is True
    assert cfg.reading_type == "pinyin"
    assert cfg.simplified_field == "Simplified;overwrite"
    assert cfg.traditional_field == "Traditional;overwrite"
    assert cfg.simp_trad_field == "Traditional,Variant;overwrite"
    assert cfg.traditional_icons is False
    assert cfg.font_size == 75
    assert cfg.cantonese_tones == ["#E60000", "#E68A00", "#00802B", "#005CE6", "#AC00E6", "gray"]
    assert cfg.mandarin_tones == ["#E60000", "#E68A00", "#00802B", "#005CE6", "gray"]
    assert cfg.use_file_references is False
    assert cfg.active_fields == []


def test_custom_values():
    raw = {
        "Profiles": ["zh", "en"],
        "BopomofoTonesToNumber": False,
        "hanziConversion": "simp",
        "readingConversion": "trad",
        "AutoCssJsGeneration": False,
        "ReadingType": "bopomofo",
        "SimplifiedField": "Simp;append",
        "TraditionalField": "Trad;append",
        "SimpTradField": "Variant;prepend",
        "traditionalIcons": True,
        "FontSize": 100,
        "CantoneseTones123456": ["red", "blue"],
        "MandarinTones12345": ["a", "b", "c"],
        "UseFileReferences": True,
        "ActiveFields": ["Sentence;1;2;;Default;Simplified", "Target Word;1;2;;None;Simplified"],
    }
    cfg = AddonConfig(_raw=raw)
    assert cfg.profiles == ["zh", "en"]
    assert cfg.hanzi_conversion == "simp"
    assert cfg.font_size == 100
    assert cfg.cantonese_tones == ["red", "blue"]
    assert cfg.mandarin_tones == ["a", "b", "c"]
    assert cfg.use_file_references is True
    assert cfg.active_fields == [
        "Sentence;1;2;;Default;Simplified",
        "Target Word;1;2;;None;Simplified",
    ]


def test_dict_fallback():
    cfg = AddonConfig(_raw={"CustomKey": "value"})
    assert cfg["CustomKey"] == "value"
    assert cfg.get("CustomKey") == "value"
    assert cfg.get("Missing", "fallback") == "fallback"


def test_keys():
    cfg = AddonConfig(_raw={"a": 1, "b": 2})
    assert list(cfg.keys()) == ["a", "b"]


def test_from_anki_missing_mw():
    class FakeMW:
        class addonManager:
            @staticmethod
            def getConfig(name):
                return {"ReadingType": "jyutping"}

    cfg = AddonConfig.from_anki(FakeMW())
    assert cfg.reading_type == "jyutping"


def test_frozen():
    cfg = AddonConfig(_raw={})
    try:
        cfg.reading_type = "bopomofo"
        assert False, "should be frozen"
    except Exception:
        pass
