from unittest.mock import MagicMock

import pytest

from config.config import AddonConfig
from reading.generator import ReadingGenerator, bopoToneToNumber


def _make_config(**overrides):
    raw = {
        "MandarinTones12345": ["#E60000", "#E68A00", "#00802B", "#005CE6", "gray"],
        "CantoneseTones123456": ["#E60000", "#E68A00", "#00802B", "#005CE6", "#AC00E6", "gray"],
        "FontSize": 75,
        "ReadingType": "pinyin",
        "AutoCssJsGeneration": True,
        "ActiveFields": [],
        "Profiles": ["all"],
        "hanziConversion": "None",
        "readingConversion": "None",
        "SimplifiedField": "Simplified;overwrite",
        "TraditionalField": "Traditional;overwrite",
        "SimpTradField": "Traditional,Variant;overwrite",
        "traditionalIcons": False,
        "BopomofoTonesToNumber": True,
    }
    raw.update(overrides)
    return AddonConfig(_raw=raw)


@pytest.fixture
def generator():
    return ReadingGenerator(db=MagicMock(), config=_make_config())


@pytest.fixture
def test_generator(test_db):
    return ReadingGenerator(db=test_db, config=_make_config())


# ── bopoToneToNumber ────────────────────────────────────────────


class TestBopoToneToNumber:
    def test_tone2_converted(self):
        assert bopoToneToNumber("ㄊㄨㄥˊ", enabled=True) == "ㄊㄨㄥ2"

    def test_tone3_converted(self):
        assert bopoToneToNumber("ㄍㄨˇ", enabled=True) == "ㄍㄨ3"

    def test_tone4_converted(self):
        assert bopoToneToNumber("ㄉㄚˋ", enabled=True) == "ㄉㄚ4"

    def test_tone5_converted(self):
        assert bopoToneToNumber("ㄉㄜ˙", enabled=True) == "ㄉㄜ5"

    def test_tone1_appended(self):
        assert bopoToneToNumber("ㄇㄚ", enabled=True) == "ㄇㄚ1"

    def test_disabled(self):
        assert bopoToneToNumber("ㄊㄨㄥˊ", enabled=False) == "ㄊㄨㄥˊ"


# ── Segment and lookup ──────────────────────────────────────────


class TestSegmentAndLookup:
    def test_simple_pinyin(self, test_generator):
        result = test_generator._segment_and_lookup("你好", "pinyin")
        assert "你好" in result
        assert "[" in result
        assert "]" in result

    def test_pinyin_format_numbered(self, test_generator):
        result = test_generator._segment_and_lookup("你好", "pinyin")
        reading = result.split("[")[1].split("]")[0]
        assert reading == "ni3 hao3", f"expected numbered pinyin, got {reading!r}"

    def test_pinyin_format_numbered_single_char(self, test_generator):
        result = test_generator._segment_and_lookup("一", "pinyin")
        reading = result.split("[")[1].split("]")[0]
        assert reading == "yi1", f"expected numbered pinyin, got {reading!r}"

    def test_mixed_text_and_chinese(self, test_generator):
        result = test_generator._segment_and_lookup("hello 你好 world", "pinyin")
        assert result.startswith("hello ")
        assert "你好" in result
        assert result.endswith(" world")

    def test_jyutping(self, test_generator):
        result = test_generator._segment_and_lookup("你好", "jyutping")
        assert "你好" in result
        assert "[" in result

    def test_unknown_char_passthrough(self, test_generator):
        result = test_generator._segment_and_lookup("hello", "pinyin")
        assert "[" not in result
        assert result == "hello"

    def test_brackets_stripped_from_input(self, test_generator):
        result = test_generator._segment_and_lookup("你好[old]", "pinyin")
        assert "old" not in result


# ── Generate ────────────────────────────────────────────────────


class TestGenerate:
    def test_returns_text_for_invalid_type(self, generator):
        result = generator.generate("你好", reading_type="invalid")
        assert result == "你好"

    def test_delegates_to_segment(self, test_generator):
        result = test_generator.generate("你好")
        assert "[" in result
