from config.config import AddonConfig


def test_defaults():
    cfg = AddonConfig(_raw={})
    assert cfg.profiles == ["all"]
    assert cfg.reading_type == "rtgs"
    assert cfg.auto_css_js_generation is True
    assert cfg.font_size == 75
    assert cfg.thai_tones == ["#E60000", "#E68A00", "#00802B", "#005CE6", "gray"]
    assert cfg.use_file_references is False
    assert cfg.active_fields == []


def test_custom_values():
    raw = {
        "Profiles": ["th", "en"],
        "ReadingType": "ipa",
        "AutoCssJsGeneration": False,
        "ThaiTones": ["red", "blue", "green", "yellow", "gray"],
        "FontSize": 100,
        "UseFileReferences": True,
        "ActiveFields": ["hover;th;Basic;Card 1;Front;rtgs"],
    }
    cfg = AddonConfig(_raw=raw)
    assert cfg.profiles == ["th", "en"]
    assert cfg.reading_type == "ipa"
    assert cfg.font_size == 100
    assert cfg.thai_tones == ["red", "blue", "green", "yellow", "gray"]
    assert cfg.use_file_references is True
    assert cfg.active_fields == ["hover;th;Basic;Card 1;Front;rtgs"]


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
                return {"ReadingType": "ipa"}

    cfg = AddonConfig.from_anki(FakeMW(), "test_addon")
    assert cfg.reading_type == "ipa"


def test_frozen():
    cfg = AddonConfig(_raw={})
    try:
        cfg.reading_type = "rtgs"
        assert False, "should be frozen"
    except Exception:
        pass
