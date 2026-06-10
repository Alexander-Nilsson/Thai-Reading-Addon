from typing import Any

import pytest

from config.config import AddonConfig
from config.mutation import (
    ConfigDelta,
    ConfigValidationError,
    LiveConfigMutation,
    ValidationError,
)


class FakeAnkiServices:
    def __init__(self):
        self.written: dict[str, dict[str, Any]] = {}

    def write_config(self, addon_module_name: str, config: dict[str, Any]) -> None:
        self.written[addon_module_name] = dict(config)


class StubModelCatalog:
    def profile_names(self):
        return ["User 1"]

    def model_names(self, profile: str):
        return {"User 1": ["Basic"]}.get(profile, [])

    def card_type_names(self, profile: str, model: str):
        if profile == "User 1" and model == "Basic":
            return ["Card 1"]
        return []

    def field_names(self, profile: str, model: str):
        if profile == "User 1" and model == "Basic":
            return ["Front", "Back"]
        return []


@pytest.fixture
def anki():
    return FakeAnkiServices()


@pytest.fixture
def defaults():
    return {
        "Profiles": ["all"],
        "ReadingType": "pinyin",
        "FontSize": 75,
    }


@pytest.fixture
def config():
    return AddonConfig(_raw={"ReadingType": "bopomofo", "FontSize": 100})


@pytest.fixture
def catalog():
    return StubModelCatalog()


@pytest.fixture
def mutation(anki, defaults, config, catalog):
    return LiveConfigMutation(anki, "test-addon", config, defaults, catalog)


# ── ConfigDelta ────────────────────────────────────────────────


class TestConfigDelta:
    def test_to_dict_skips_none(self):
        d = ConfigDelta().to_dict()
        assert d == {}

    def test_to_dict_reading_type(self):
        d = ConfigDelta(reading_type="jyutping").to_dict()
        assert d == {"ReadingType": "jyutping"}

    def test_to_dict_tuple_to_list(self):
        d = ConfigDelta(mandarin_tones=("#fff", "#000", "#111", "#222", "#333")).to_dict()
        assert d["MandarinTones12345"] == ["#fff", "#000", "#111", "#222", "#333"]

    def test_to_dict_profiles(self):
        d = ConfigDelta(profiles=["User 1", "User 2"]).to_dict()
        assert d["Profiles"] == ["User 1", "User 2"]

    def test_from_dict_round_trip(self):
        raw = {
            "ReadingType": "jyutping",
            "FontSize": 90,
            "MandarinTones12345": ["red", "green", "blue", "yellow", "gray"],
            "ActiveFields": ["hover;all;Basic;Card 1;Front;Both"],
        }
        delta = ConfigDelta.from_dict(raw)
        assert delta.reading_type == "jyutping"
        assert delta.font_size == 90
        assert delta.mandarin_tones == ("red", "green", "blue", "yellow", "gray")
        assert delta.active_fields == ("hover;all;Basic;Card 1;Front;Both",)

    def test_from_dict_ignores_unknown_keys(self):
        delta = ConfigDelta.from_dict({"UnknownKey": "value"})
        assert delta.reading_type is None

    def test_from_dict_to_dict_round_trip(self):
        original = ConfigDelta(
            reading_type="bopomofo",
            font_size=50,
            mandarin_tones=("#E60000", "#E68A00", "#00802B", "#005CE6", "gray"),
            active_fields=("hover;all;Basic;Card 1;Front;Both;pinyin",),
        )
        as_dict = original.to_dict()
        restored = ConfigDelta.from_dict(as_dict)
        assert restored.reading_type == original.reading_type
        assert restored.font_size == original.font_size
        assert restored.mandarin_tones == original.mandarin_tones
        assert restored.active_fields == original.active_fields


# ── LiveConfigMutation.validate ────────────────────────────────


class TestValidate:
    def test_empty_delta_passes(self, mutation):
        assert mutation.validate(ConfigDelta()) == []

    def test_rejects_bad_reading_type(self, mutation):
        errs = mutation.validate(ConfigDelta(reading_type="xyz"))
        assert len(errs) == 1
        assert errs[0].field == "reading_type"
        assert "xyz" in errs[0].message

    def test_accepts_valid_reading_types(self, mutation):
        for rt in ("pinyin", "bopomofo", "jyutping"):
            errs = mutation.validate(ConfigDelta(reading_type=rt))
            assert errs == [], f"failed for {rt}"

    def test_rejects_bad_hanzi_conversion(self, mutation):
        errs = mutation.validate(ConfigDelta(hanzi_conversion="Invalid"))
        assert len(errs) == 1
        assert errs[0].field == "hanzi_conversion"

    def test_rejects_bad_reading_conversion(self, mutation):
        errs = mutation.validate(ConfigDelta(reading_conversion="Invalid"))
        assert len(errs) == 1
        assert errs[0].field == "reading_conversion"

    def test_rejects_font_size_too_low(self, mutation):
        errs = mutation.validate(ConfigDelta(font_size=0))
        assert len(errs) == 1
        assert errs[0].field == "font_size"

    def test_rejects_font_size_too_high(self, mutation):
        errs = mutation.validate(ConfigDelta(font_size=201))
        assert len(errs) == 1

    def test_accepts_valid_font_size(self, mutation):
        errs = mutation.validate(ConfigDelta(font_size=75))
        assert errs == []

    def test_rejects_wrong_mandarin_tone_count(self, mutation):
        errs = mutation.validate(ConfigDelta(mandarin_tones=("#000", "#111")))
        assert len(errs) == 1
        assert errs[0].field == "mandarin_tones"

    def test_rejects_wrong_cantonese_tone_count(self, mutation):
        errs = mutation.validate(ConfigDelta(cantonese_tones=("#000",)))
        assert len(errs) == 1
        assert errs[0].field == "cantonese_tones"

    def test_rejects_invalid_active_field_syntax(self, mutation):
        errs = mutation.validate(ConfigDelta(active_fields=("garbage",)))
        assert len(errs) == 1
        assert errs[0].field == "active_fields"

    def test_allows_active_field_with_missing_note_type(self, mutation):
        errs = mutation.validate(ConfigDelta(active_fields=("hover;User 1;MissingNote;Card 1;Front;Both;pinyin",)))
        assert errs == []

    def test_allows_active_field_with_missing_card_type(self, mutation):
        errs = mutation.validate(ConfigDelta(active_fields=("hover;User 1;Basic;MissingCard;Front;Both;pinyin",)))
        assert errs == []

    def test_allows_active_field_with_missing_field(self, mutation):
        errs = mutation.validate(ConfigDelta(active_fields=("hover;User 1;Basic;Card 1;MissingField;Both;pinyin",)))
        assert errs == []

    def test_accepts_valid_active_field(self, mutation):
        errs = mutation.validate(ConfigDelta(active_fields=("hover;User 1;Basic;Card 1;Front;Both;pinyin",)))
        assert errs == []

    def test_accepts_all_profile_active_field(self, mutation):
        errs = mutation.validate(ConfigDelta(active_fields=("reading;all;Basic;Card 1;Front;Both;default",)))
        assert errs == []

    def test_accumulates_multiple_errors(self, mutation):
        errs = mutation.validate(
            ConfigDelta(
                reading_type="invalid",
                font_size=999,
                mandarin_tones=("#000",),
            )
        )
        assert len(errs) == 3


# ── LiveConfigMutation.save_config ──────────────────────────────


class TestSaveConfig:
    def test_saves_and_returns_config(self, mutation, anki):
        result = mutation.save_config(ConfigDelta(reading_type="jyutping"))
        assert result.reading_type == "jyutping"
        assert anki.written["test-addon"]["ReadingType"] == "jyutping"

    def test_merge_preserves_other_keys(self, mutation, anki):
        result = mutation.save_config(ConfigDelta(font_size=50))
        assert result.font_size == 50
        assert result.reading_type == "bopomofo"  # from original config

    def test_merge_fills_from_defaults(self, mutation, anki):
        result = mutation.save_config(ConfigDelta())
        assert result.font_size == 100  # from config, not defaults
        assert result.reading_type == "bopomofo"  # from config

    def test_raises_on_invalid(self, mutation):
        with pytest.raises(ConfigValidationError) as exc:
            mutation.save_config(ConfigDelta(reading_type="bogus"))
        assert len(exc.value.errors) == 1

    def test_updates_internal_config(self, mutation):
        mutation.save_config(ConfigDelta(reading_type="jyutping"))
        assert mutation._config.reading_type == "jyutping"


# ── ValidationError ─────────────────────────────────────────────


class TestValidationError:
    def test_equality(self):
        e1 = ValidationError("field", "msg")
        assert e1.field == "field"
        assert e1.message == "msg"

    def test_in_config_validation_error(self):
        errs = [ValidationError("a", "bad a"), ValidationError("b", "bad b")]
        exc = ConfigValidationError(errs)
        assert exc.errors == errs
        assert "bad a" in str(exc)
        assert "bad b" in str(exc)
